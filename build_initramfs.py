#!/usr/bin/env python3
"""Pack work/rootfs (+ symlinks/modes from rootfs_manifest.tsv) into a gzip'd
cpio 'newc' initramfs, adding our own /init that brings the robot userland up.
Usage: build_initramfs.py <rootfs_dir> <manifest.tsv> <init_script> <out.cpio.gz>
"""
import gzip
import os
import sys

rootfs, manifest, init_script, out = sys.argv[1:5]
ino = [1]


def hdr(name, mode, size, nlink=1, rdev=(0, 0)):
    ino[0] += 1
    nb = name.encode() + b"\0"
    f = "070701" + "".join(
        f"{v:08X}"
        for v in (ino[0], mode, 0, 0, nlink, 0, size, 0, 0, rdev[0], rdev[1], len(nb), 0)
    )
    h = f.encode() + nb
    return h + b"\0" * (-len(h) % 4)


def pad(b):
    return b + b"\0" * (-len(b) % 4)


modes, links, dev = {}, {}, []
for line in open(manifest, encoding="utf-8"):
    k, p, v = line.rstrip("\n").split("\t", 2)
    if k == "F":
        modes[p] = int(v, 8)
    elif k == "L":
        links[p] = v
    elif k == "O":
        dev.append((p, int(v, 8)))

with gzip.open(out, "wb", compresslevel=6) as z:
    seen = set()

    def w(b):
        z.write(b)

    def add_dir(rel):
        if rel in seen or rel == "":
            return
        add_dir(rel.rsplit("/", 1)[0] if "/" in rel else "")
        seen.add(rel)
        w(hdr(rel, 0o040755, 0, 2))

    for dp, dn, fn in os.walk(rootfs):
        rel = os.path.relpath(dp, rootfs).replace("\\", "/")
        rel = "" if rel == "." else rel
        add_dir(rel)
        for n in fn:
            r = (rel + "/" + n) if rel else n
            if r == "init":
                continue
            data = open(os.path.join(dp, n), "rb").read()
            m = 0o100000 | (modes.get("/" + r, 0o644) & 0o7777)
            w(hdr(r, m, len(data)))
            w(pad(data))
    for p, tgt in links.items():
        r = p.lstrip("/")
        add_dir(r.rsplit("/", 1)[0] if "/" in r else "")
        t = tgt.encode()
        w(hdr(r, 0o120777, len(t)))
        w(pad(t))
    for d in ("proc", "sys", "dev", "tmp", "run", "var/run", "var/lock", "var/log", "var/volatile"):
        add_dir(d)
    data = open(init_script, "rb").read().replace(b"\r\n", b"\n")
    w(hdr("init", 0o100755, len(data)))
    w(pad(data))
    w(hdr("TRAILER!!!", 0, 0))
print("wrote", out, os.path.getsize(out) // 1048576, "MiB")
