import sys,re
from PySquashfsImage import SquashFsImage
img=SquashFsImage.from_file(sys.argv[1])
paths=[(it.path,it.is_dir) for it in img]
print('top-level:',sorted({p.split('/')[1] for p,_ in paths if p.count('/')>=1 and p!='/'}))
pat=re.compile(sys.argv[2],re.I)
for p,d in paths:
    if pat.search(p): print(('D ' if d else 'F ')+p)
