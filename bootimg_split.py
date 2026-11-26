"""Split an Android boot image (header v0) into kernel, ramdisk and device-tree
parts, print its kernel command line, and pull the version string and embedded
config out of a gzip-compressed kernel when present.

Usage: python -I bootimg_split.py boot.img out_dir
"""
import gzip
import os
import re
import struct
import sys
import zlib

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
d = open(src, 'rb').read()
if d[:8] != b'ANDROID!':
    sys.exit('not an Android boot image')

(ksz, kaddr, rsz, raddr, ssz, saddr, taddr, page, dtsz, osver) = struct.unpack('<10I', d[8:48])
cmdline = d[64:64 + 512].split(b'\0')[0].decode(errors='replace')
extra = d[64 + 512 + 32:64 + 512 + 32 + 1024].split(b'\0')[0].decode(errors='replace')
print('kernel size', ksz, 'addr', hex(kaddr))
print('ramdisk size', rsz, 'second size', ssz, 'dt size', dtsz, 'page size', page)
print('cmdline:', cmdline)
if extra:
    print('extra cmdline:', extra)


def pages(n):
    return (n + page - 1) // page


off = page
kernel = d[off:off + ksz]
off += pages(ksz) * page
ramdisk = d[off:off + rsz]
off += pages(rsz) * page
off += pages(ssz) * page
dt = d[off:off + dtsz]

open(os.path.join(out, 'kernel.bin'), 'wb').write(kernel)
open(os.path.join(out, 'ramdisk.gz'), 'wb').write(ramdisk)
open(os.path.join(out, 'dt.bin'), 'wb').write(dt)
open(os.path.join(out, 'cmdline.txt'), 'w').write(cmdline + '\n' + extra + '\n')

# A zImage carries its kernel as a gzip stream after a short decompressor stub.
for m in re.finditer(rb'\x1f\x8b\x08', kernel):
    try:
        img = zlib.decompressobj(31).decompress(kernel[m.start():])
    except zlib.error:
        continue
    if len(img) < 2_000_000:
        continue
    open(os.path.join(out, 'Image.raw'), 'wb').write(img)
    ver = re.search(rb'Linux version [^\n\0]{0,200}', img)
    print('kernel:', ver.group().decode(errors='replace') if ver else 'version string not found')
    i = img.find(b'IKCFG_ST')
    if i >= 0:
        j = img.find(b'IKCFG_ED', i)
        open(os.path.join(out, 'kernel_config.txt'), 'w').write(gzip.decompress(img[i + 8:j]).decode())
        print('wrote kernel_config.txt')
    break
