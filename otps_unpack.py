#!/usr/bin/env python3
"""Read-only parser for 'Otps' (otagen v2.0) OTA containers.

Container = b'Otps' + 4 bytes, then a flat sequence of chunks:
    tag[4] + length[4, little endian] + payload[length]
Container chunks (Sdat, Otpc, Otim) nest more chunks. Everything else is a leaf.

Usage: python -I otps_unpack.py <package.signed> [outdir]
Without outdir it only prints the tree.
"""
import os
import struct
import sys

CONTAINERS = {b"Sdat", b"Otpc", b"Otim", b"Otie"}


def walk(f, pos, end, depth, out, path):
    idx = 0
    while pos + 8 <= end:
        f.seek(pos)
        tag = f.read(4)
        (ln,) = struct.unpack("<I", f.read(4))
        body = pos + 8
        if body + ln > end:
            print(f"{'  ' * depth}!! bad chunk {tag!r} len={ln} at {pos}")
            return
        name = f"{path}/{idx:02d}_{tag.decode('latin1')}"
        head = f.read(min(ln, 24))
        if tag in CONTAINERS:
            print(f"{'  ' * depth}{tag.decode()} @{pos} len={ln}")
            walk(f, body, body + ln, depth + 1, out, name)
        else:
            print(f"{'  ' * depth}{tag.decode('latin1')} @{pos} len={ln} {head[:16].hex()}")
            if out and ln > 4096:
                dest = os.path.join(out, name.lstrip("/").replace("/", "__") + ".bin")
                os.makedirs(out, exist_ok=True)
                f.seek(body)
                with open(dest, "wb") as o:
                    left = ln
                    while left:
                        chunk = f.read(min(left, 1 << 20))
                        o.write(chunk)
                        left -= len(chunk)
                print(f"{'  ' * depth}  -> {dest}")
        pos = body + ln
        idx += 1


def main():
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    size = os.path.getsize(src)
    with open(src, "rb") as f:
        assert f.read(4) == b"Otps", "not an Otps container"
        walk(f, 8, size, 0, out, "")


if __name__ == "__main__":
    main()
