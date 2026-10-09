"""Build a station in the emulator and save state/bitmap.  usage: station.py N out.png [frames]"""
import os as _os, sys as _sys
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
for _d in ('tools', 'emulator', 'web/tools'):
    if _os.path.join(REPO, _d) not in _sys.path: _sys.path.insert(0, _os.path.join(REPO, _d))

import sys, os, pickle
from emu import Atari
from render import render_bitmap
def build(n, frames=250, zone=1):
    at = Atari()
    for i in range(400): at.run_frame()
    state = {'done': False}
    def hook(at_, pc):
        if pc == 0xA241 and not state['done'] and at_.ram[0xE2] == 0:
            at_.ram[0xB7] = n; at_.ram[0xB8] = zone; state['done'] = True
    at.consol = 6
    for i in range(20): at.run_frame(hook)
    at.consol = 7
    for i in range(frames): at.run_frame(hook)
    return at
if __name__ == '__main__':
    n = int(sys.argv[1]); at = build(n, int(sys.argv[3]) if len(sys.argv) > 3 else 250)
    render_bitmap(at.ram).save(sys.argv[2])
    pickle.dump(bytes(at.ram), open(sys.argv[2] + '.ram', 'wb'))
    print('station', at.ram[0xB7], 'sections', at.ram[0xF6], 'pc %04X' % at.cpu.pc)
