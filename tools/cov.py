import os as _os, sys as _sys
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
for _d in ('tools', 'emulator', 'web/tools'):
    if _os.path.join(REPO, _d) not in _sys.path: _sys.path.insert(0, _os.path.join(REPO, _d))

import sys,os,random,pickle; from emu import Atari
random.seed(1)
at=Atari()
cov=bytearray(0x10000)
def runf(n):
    for i in range(n):
        at.run_frame()
runf(1500)          # attract
print('attract pc %04X, covered %d'%(at.cpu.pc,sum(at.cover[0x8000:0xC000])))
for game in range(2):
    at.consol=6; runf(10); at.consol=7; runf(200)
    for k in range(3000):
        if k%20==0:
            at.joy=random.choice([0xF,0xE,0xD,0xB,0x7,0x7,0xB,0xA,0x6,0x9,0x5])
            at.trig=0 if random.random()<0.2 else 1
        runf(1)
    print('game',game,'covered %d'%sum(at.cover[0x8000:0xC000]), 'ram code', sum(at.cover[0:0x8000]))
pickle.dump(bytes(at.cover),open('cover.pkl','wb'))
