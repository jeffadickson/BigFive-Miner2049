import os as _os, sys as _sys
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
for _d in ('tools', 'emulator', 'web/tools'):
    if _os.path.join(REPO, _d) not in _sys.path: _sys.path.insert(0, _os.path.join(REPO, _d))

import sys
d=open(_os.path.join(REPO, 'rom/miner.rom'),'rb').read()
def rb(a): return d[a-0x8000]
def dl(a, n=60):
    out=[]
    for i in range(n):
        b=rb(a); s='%04X %02X '%(a,b)
        m=b&15
        if m==0: s+='blank %d'%(((b>>4)&7)+1); a+=1
        elif m==1:
            t=rb(a+1)|rb(a+2)<<8; s+=('JVB' if b&0x40 else 'JMP')+' $%04X'%t; a+=3
            out.append(s+(' DLI' if b&0x80 else '')); break
        else:
            s+='mode %X'%m
            if b&0x40: s+=' LMS $%04X'%(rb(a+1)|rb(a+2)<<8); a+=3
            else: a+=1
            if b&0x10: s+=' HSCROL'
            if b&0x20: s+=' VSCROL'
        if b&0x80: s+=' DLI'
        out.append(s)
    return out
if __name__=='__main__':
    print('\n'.join(dl(int(sys.argv[1],16), int(sys.argv[2]) if len(sys.argv)>2 else 60)))
