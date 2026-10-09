import os as _os, sys as _sys
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
for _d in ('tools', 'emulator', 'web/tools'):
    if _os.path.join(REPO, _d) not in _sys.path: _sys.path.insert(0, _os.path.join(REPO, _d))

import sys,os,random; from emu import Atari
def boot(frames=200):
    at=Atari()
    for i in range(frames): at.run_frame()
    return at
def press_start(at):
    at.consol=6
    for i in range(5): at.run_frame()
    at.consol=7
def zp(at,a): return at.ram[a]
if __name__=='__main__':
    at=boot(100)
    press_start(at)
    for f in range(400):
        at.run_frame()
        if f%20==0:
            print(f, 'B7=%d B8=%d B9=%d E2=%02X A6=%d F6=%d F8=%02X X=%02X Y=%02X fr=%d A3=%d 9D=%02X'%tuple(at.ram[a] for a in (0xB7,0xB8,0xB9,0xE2,0xA6,0xF6,0xF8,0x90,0x91,0x92,0xA3,0x9D)), 'score',''.join(str(at.ram[0xBA+i]) for i in range(7)))
