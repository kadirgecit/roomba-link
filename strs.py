import re,sys
d=open(sys.argv[1],'rb').read()
pat=re.compile(rb'[\x20-\x7e]{%d,}'%int(sys.argv[2]))
for m in pat.finditer(d): print(m.group().decode())
