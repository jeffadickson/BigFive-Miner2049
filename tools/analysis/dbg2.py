import os as _os, sys as _sys
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '../..'))
for _d in ('tools', 'emulator', 'web/tools'):
    if _os.path.join(REPO, _d) not in _sys.path: _sys.path.insert(0, _os.path.join(REPO, _d))

import sys
src=open('claimtest.py').read(); src=src[:src.index('at=build(1,250)')]
ns={}; exec(compile(src,'ct','exec'),ns)
from station import build
at=build(1,250); base=bytes(at.ram)
import re
labels={}
for l in open(_os.path.join(REPO, 'src/annot/85_world.txt')):
    m=re.match(r'L (\w{4}) (\w+)',l)
    if m: labels[int(m.group(1),16)]=m.group(2)
for l in open(_os.path.join(REPO, 'src/annot/40_draw.txt')):
    m=re.match(r'L (\w{4}) (\w+)',l)
    if m: labels[int(m.group(1),16)]=m.group(2)
bx,by,fr=0x34,114,1
at.ram[0x90]=bx; at.ram[0x91]=by; at.ram[0x92]=fr; at.ram[0xFE]=7
for a in (0xFF,0xB4,0x93,0xAA,0xA3): at.ram[a]=0
c=at.cpu; sent=0xF060; c.stPush((sent-1)>>8); c.stPush((sent-1)&0xFF); c.pc=0xB625
while c.pc!=sent:
    if c.pc in labels and labels[c.pc].startswith(('CA_','CLAIM','PLOT_XY','CF_')): print(labels[c.pc],'X=%02X Y=%02X PLOT_X=%02X PLOT_Y=%d A=%02X'%(c.x,c.y,at.ram[0x85],at.ram[0x86],c.a))
    c.step()
