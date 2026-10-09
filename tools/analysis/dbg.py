import os as _os, sys as _sys
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '../..'))
for _d in ('tools', 'emulator', 'web/tools'):
    if _os.path.join(REPO, _d) not in _sys.path: _sys.path.insert(0, _os.path.join(REPO, _d))

import sys
src=open('claimtest.py').read(); src=src[:src.index('at=build(1,250)')]
ns={}; exec(compile(src,'ct','exec'),ns)
from station import build
at=build(1,250); base=bytes(at.ram)
for (bx,by,fr) in [(0x34,114,1),(0xb6,148,1),(0x54,32,2)]:
    at.ram[:]=base
    at.ram[0x90]=bx; at.ram[0x91]=by; at.ram[0x92]=fr; at.ram[0xFE]=7
    for a in (0xFF,0xB4,0x93,0xAA,0xA3): at.ram[a]=0
    py=bytearray(at.ram)
    ns['call'](at,0xB625); ns['claim_floor'](py)
    print('case',hex(bx),by,fr,'feet',ns['FEET'][2*fr:2*fr+2])
    ys=[y for y in range(8,192) if any(ns['read_px'](at.ram,x,y)!=ns['read_px'](py,x,y) for x in range(0x30,0xD0))]
    print('diff lines',ys)
    for yy in ys:
        f=lambda r:''.join('.123'[ns['read_px'](r,xx,yy)] for xx in range(0x30,0xD0))
        print(yy,"\n",f(base),"\n",f(at.ram),"\n",f(py))
