"""Minimal Atari 400/800 harness around py65 for code-coverage and RAM snapshots.

Models only what Miner 2049er touches: ANTIC (VCOUNT, WSYNC, NMIs incl. DLIs from the
display list), POKEY RANDOM/keyboard, PIA joystick, GTIA triggers/console keys.
Collision registers read 0.  OS is replaced by a tiny NMI dispatcher equivalent to the
400/800 OS one (DLI -> JMP (VDSLST); VBI -> push A,X,Y; JMP (VVBLKI)).
"""
import os as _os, sys as _sys
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
for _d in ('tools', 'emulator', 'web/tools'):
    if _os.path.join(REPO, _d) not in _sys.path: _sys.path.insert(0, _os.path.join(REPO, _d))

import sys, random, os
from py65.devices.mpu6502 import MPU

ROMF = os.environ.get('ROM', _os.path.join(REPO, 'rom/miner.rom'))
CART = open(ROMF, 'rb').read()

class Mem(bytearray):
    pass

class Atari:
    def __init__(self):
        self.ram = bytearray(0x10000)
        self.ram[0x8000:0xC000] = CART
        # fake OS: $F800.. must not look like a 5200 font
        for i in range(0xC000, 0x10000): self.ram[i] = 0xEA
        fp = _os.path.join(REPO, 'rom/altirra_font.bin')
        if os.path.exists(fp): self.ram[0xE000:0xE400] = open(fp, 'rb').read()
        stub = [0x2C, 0x0F, 0xD4,        # F000 BIT NMIST
                0x10, 0x03,              # BPL vbi
                0x6C, 0x00, 0x02,        # JMP (VDSLST)
                0x48, 0x8A, 0x48, 0x98, 0x48,  # vbi: PHA TXA PHA TYA PHA
                0x6C, 0x22, 0x02]        # JMP (VVBLKI)
        self.ram[0xF000:0xF000 + len(stub)] = bytes(stub)
        self.ram[0xFFFA] = 0x00; self.ram[0xFFFB] = 0xF0
        self.ram[0xFFFC] = 0xB5; self.ram[0xFFFD] = 0xA1   # straight into the diagnostic init
        self.ram[0xFFFE] = 0x40; self.ram[0xFFFF] = 0xF0   # IRQ -> RTI
        self.ram[0xF040] = 0x40
        self.cpu = MPU(memory=self, pc=0xA1B5)
        self.cycles = 0
        self.line = 0
        self.nmien = 0
        self.nmist = 0x1F
        self.dlist = 0
        self.dli_lines = set()
        self.joy = 0x0F   # PORTA low nibble, active low
        self.trig = 1
        self.consol = 7
        self.kbcode = 0xFF
        self.skstat = 0xFF
        self.cover = bytearray(0x10000)
        self.writes = {}
        self.hw_w = {}
        self.hw_r = {}
        self.frame = 0
        self.ram_exec_src = {}   # RAM addr -> ROM source (for relocated code)

    # memory interface for py65
    def __len__(self): return 0x10000
    def __getitem__(self, a):
        if isinstance(a, slice):
            return [self[i] for i in range(*a.indices(0x10000))]
        if 0xD000 <= a < 0xD800:
            return self.ioread(a)
        return self.ram[a]
    def __setitem__(self, a, v):
        if isinstance(a, slice):
            for i, x in zip(range(*a.indices(0x10000)), v): self[i] = x
            return
        if 0xD000 <= a < 0xD800:
            self.iowrite(a, v); return
        if a < 0x8000:
            self.ram[a] = v

    def ioread(self, a):
        self.hw_r[a] = self.hw_r.get(a, 0) + 1
        if a == 0xD40B: return (self.line >> 1) & 0xFF
        if a == 0xD40F: return self.nmist
        if 0xD200 <= a < 0xD300:
            r = a & 0x0F
            if r == 0x0A: return random.randrange(256)
            if r == 0x09: return self.kbcode
            if r == 0x0F: return self.skstat
            return 0xFF
        if 0xD300 <= a < 0xD400:
            if (a & 3) == 0: return 0xF0 | self.joy
            return 0xFF
        if 0xD000 <= a < 0xD100:
            r = a & 0x1F
            if r == 0x10: return self.trig
            if r in (0x11, 0x12, 0x13): return 1
            if r == 0x1F: return self.consol
            if r == 0x14: return 0x0F  # PAL: NTSC
            return 0
        return 0xFF

    def iowrite(self, a, v):
        self.hw_w[a] = self.hw_w.get(a, 0) + 1
        if a == 0xD40A:   # WSYNC
            self.cycles = (self.cycles // 114 + 1) * 114
        elif a == 0xD40E: self.nmien = v
        elif a == 0xD40F: self.nmist = 0x1F
        elif a == 0xD402: self.dlist = (self.dlist & 0xFF00) | v
        elif a == 0xD403: self.dlist = (self.dlist & 0xFF) | v << 8

    def parse_dlist(self):
        lines = set(); y = 8; a = self.dlist; n = 0
        while y < 248 and n < 300:
            ins = self.ram[a]; n += 1
            mode = ins & 0x0F
            if mode == 0:
                h = ((ins >> 4) & 7) + 1; a += 1
            elif mode == 1:
                if ins & 0x40: break
                a = self.ram[a + 1] | self.ram[a + 2] << 8; continue
            else:
                h = {2: 8, 3: 10, 4: 8, 5: 16, 6: 8, 7: 16, 8: 8, 9: 4, 10: 4, 11: 2, 12: 1, 13: 2, 14: 1, 15: 1}[mode]
                a += 3 if ins & 0x40 else 1
            y += h
            if ins & 0x80: lines.add(y - 1)
        return lines

    def nmi(self, kind):
        self.nmist = 0x80 if kind == 'dli' else 0x40
        c = self.cpu
        c.stPushWord(c.pc); c.stPush(c.p & ~c.BREAK | c.UNUSED)
        c.p |= c.INTERRUPT
        c.pc = 0xF000

    def run_frame(self, hook=None):
        c = self.cpu
        self.dli_lines = self.parse_dlist()
        line_end = 0
        for self.line in range(262):
            if self.line in self.dli_lines and self.nmien & 0x80:
                self.nmi('dli')
            if self.line == 248 and self.nmien & 0x40:
                self.nmi('vbi')
            target = (self.frame * 262 + self.line + 1) * 114
            while self.cycles < target:
                pc = c.pc
                self.cover[pc] = 1
                c.step()
                self.cycles += 3   # crude average
                if hook: hook(self, pc)
        self.frame += 1

if __name__ == '__main__':
    import time
    at = Atari()
    t = time.time()
    for f in range(60): at.run_frame()
    print('60 frames in %.1fs pc=%04X' % (time.time() - t, at.cpu.pc))
