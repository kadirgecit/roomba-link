"""Find every flattened device tree (FDT) blob embedded in a file, such as a
kernel image with appended device trees, and decompile each one to text.

Usage: python -I fdt_dump.py kernel.bin out_dir
"""
import os
import struct
import sys

src, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
d = open(src, 'rb').read()
MAGIC = b'\xd0\x0d\xfe\xed'


def find_all(b, m):
    i = 0
    while True:
        i = b.find(m, i)
        if i < 0:
            return
        yield i
        i += 1


def be32(b, o):
    return struct.unpack('>I', b[o:o + 4])[0]


def cstr(b, o):
    return b[o:b.index(b'\0', o)].decode('utf-8', 'replace')


def fmt_prop(name, val):
    if not val:
        return name + ';'
    try:
        s = val.decode('ascii')
        if s.endswith('\0') and all(32 <= ord(c) < 127 or c == '\0' for c in s[:-1]) and '\0\0' not in s:
            parts = s[:-1].split('\0')
            if all(parts):
                return name + ' = ' + ', '.join('"%s"' % p for p in parts) + ';'
    except UnicodeDecodeError:
        pass
    if len(val) % 4 == 0:
        cells = struct.unpack('>%dI' % (len(val) // 4), val)
        return name + ' = <' + ' '.join('0x%x' % c for c in cells) + '>;'
    return name + ' = [' + val.hex() + '];'


def decompile(blob):
    pos, off_str = be32(blob, 8), be32(blob, 12)
    out, depth = [], 0
    while True:
        tok = be32(blob, pos)
        pos += 4
        if tok == 1:
            name = cstr(blob, pos)
            pos = (pos + len(name) + 1 + 3) & ~3
            out.append('  ' * depth + (name or '/') + ' {')
            depth += 1
        elif tok == 2:
            depth -= 1
            out.append('  ' * depth + '};')
        elif tok == 3:
            ln, nameoff = be32(blob, pos), be32(blob, pos + 4)
            pos += 8
            val = blob[pos:pos + ln]
            pos = (pos + ln + 3) & ~3
            out.append('  ' * depth + fmt_prop(cstr(blob, off_str + nameoff), val))
        elif tok == 4:
            continue
        elif tok == 9:
            break
        else:
            out.append('/* bad token %x */' % tok)
            break
    return '\n'.join(out)


n = 0
for off in find_all(d, MAGIC):
    total, ver = be32(d, off + 4), be32(d, off + 20)
    if total < 0x100 or total > 0x400000 or ver < 16 or ver > 17:
        continue
    try:
        txt = decompile(d[off:off + total])
    except (struct.error, ValueError) as e:
        print('skip blob at', hex(off), e)
        continue
    model = next((l.strip() for l in txt.split('\n') if l.strip().startswith('model =')), None)
    open(os.path.join(outdir, 'dt_%02d_0x%x.dts' % (n, off)), 'w').write(txt)
    print(n, hex(off), total, model)
    n += 1
print('blobs:', n)
