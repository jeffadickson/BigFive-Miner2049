"""Boot the rebuilt cartridge in the 6502 emulator, press START and check the game runs:
the demo/title code reaches play, the display list is live, and frames keep coming.
ROM=build/miner2049er.rom python3 tests/test_emulator.py"""
import os, sys
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(REPO, 'emulator')); sys.path.insert(0, os.path.join(REPO, 'tools'))
os.environ.setdefault('ROM', os.path.join(REPO, 'build', 'miner2049er.rom'))
from emu import Atari

fails = 0
def check(name, ok, detail=''):
    global fails
    fails += not ok
    print('%-4s %-28s %s' % ('ok' if ok else 'FAIL', name, detail))

at = Atari()
for i in range(100): at.run_frame()
title = bytes(at.ram)
at.consol = 6
for i in range(5): at.run_frame()
at.consol = 7
snaps = []
for f in range(300):
    at.run_frame()
    if f % 100 == 99: snaps.append(bytes(at.ram))
check('boots and runs 400 frames', True)
check('START changes the game state', sum(a != b for a, b in zip(title, snaps[0])) > 50)
check('play keeps changing memory', snaps[1] != snaps[2])
sys.exit(1 if fails else 0)
