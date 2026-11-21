#!/usr/bin/env python3
"""Extract a SquashFS rootfs on Windows. Regular files are written out; symlinks
and device nodes (which Windows can't hold) are recorded in manifest.tsv instead.
Usage: extract_rootfs.py <image> <outdir>
"""
import os
import sys

from PySquashfsImage import SquashFsImage

src, out = sys.argv[1], sys.argv[2]
img = SquashFsImage.from_file(src)
os.makedirs(out, exist_ok=True)
manifest = open(os.path.join(os.path.dirname(out.rstrip("/\\")) or ".", "rootfs_manifest.tsv"), "w", encoding="utf-8")
counts = {"file": 0, "dir": 0, "link": 0, "other": 0, "err": 0}
for it in img:
    p = it.path
    if p == "/":
        continue
    dest = os.path.join(out, *p.strip("/").split("/"))
    try:
        if it.is_dir:
            os.makedirs(dest, exist_ok=True)
            counts["dir"] += 1
        elif it.is_symlink:
            manifest.write(f"L\t{p}\t{it.readlink() if hasattr(it, 'readlink') else it.read_bytes().decode()}\n")
            counts["link"] += 1
        elif it.is_file:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as o:
                o.write(it.read_bytes())
            manifest.write(f"F\t{p}\t{oct(it.mode & 0o7777)}\n")
            counts["file"] += 1
        else:
            manifest.write(f"O\t{p}\t{it.mode:o}\n")
            counts["other"] += 1
    except Exception as e:  # keep going, record the problem
        manifest.write(f"E\t{p}\t{e}\n")
        counts["err"] += 1
print(counts)
