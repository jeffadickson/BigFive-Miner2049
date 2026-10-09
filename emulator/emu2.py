"""Harness with a scan-line renderer and GTIA collision model, for making exact movies of the game screen.

Renders ANTIC modes 2 (text) and E (bitmap) and blank lines, players/missiles in single-line
resolution with HPOS/SIZE, PRIOR $31-style priority (players over playfield, fifth player,
multicolour P0|P1), and accumulates the collision registers line by line so the game's own
collision code works. Register values are sampled at the end of each line's CPU slice.
"""
import os as _os, sys as _sys
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
for _d in ('tools', 'emulator', 'web/tools'):
    if _os.path.join(REPO, _d) not in _sys.path: _sys.path.insert(0, _os.path.join(REPO, _d))

import sys, os
import numpy as np
from emu import Atari
from render import atari_rgb

PALETTE = np.array([atari_rgb(c) for c in range(256)], dtype=np.uint8)
X0, XW = 44, 168          # colour clocks shown: 44 .. 211 (like atari800's 336-pixel window)
Y0, YH = 16, 224           # scan lines shown (matches the atari800 window)

class Atari2(Atari):
    def __init__(self):
        super().__init__()
        self.g = [0] * 32          # GTIA write registers
        self.antic = {}            # ANTIC write registers
        self.coll = [0] * 16       # read: M0PF..M3PF, P0PF..P3PF, M0PL..M3PL, P0PL..P3PL
        self.frame_rgb = np.zeros((YH, XW * 2, 3), np.uint8)
        self.font = None
        self.render_on = True

    def ioread(self, a):
        if 0xD000 <= a < 0xD010:
            return self.coll[a & 0x0F]
        return super().ioread(a)

    def iowrite(self, a, v):
        if 0xD000 <= a < 0xD020:
            r = a & 0x1F
            if r == 0x1E: self.coll = [0] * 16       # HITCLR
            self.g[r] = v
            self.hw_w[a] = self.hw_w.get(a, 0) + 1
            return
        if 0xD400 <= a < 0xD410:
            self.antic[a & 0x0F] = v
        super().iowrite(a, v)

    # ------------------------------------------------------------ display list walk (per frame)
    def dl_lines(self):
        """list of (scanline, mode, data_address, row_in_mode_line) for scan lines 8..247"""
        out = {}; y = 8; a = self.dlist; mem = None; n = 0
        ram = self.ram
        while y < 248 and n < 400:
            ins = ram[a]; n += 1; mode = ins & 0x0F
            if mode == 0:
                h = ((ins >> 4) & 7) + 1; a += 1
                for k in range(h): out[y + k] = (0, 0, 0)
                y += h; continue
            if mode == 1:
                if ins & 0x40:
                    break
                a = ram[a + 1] | ram[a + 2] << 8; continue
            if ins & 0x40:
                mem = ram[a + 1] | ram[a + 2] << 8; a += 3
            else:
                a += 1
            h = {2: 8, 6: 8, 7: 16, 14: 1, 15: 1, 13: 2, 12: 1, 4: 8, 5: 16}.get(mode, 1)
            for k in range(h): out[y + k] = (mode, mem, k)
            per = {2: 40, 14: 40, 15: 40, 6: 20, 7: 20, 13: 40, 12: 20, 4: 40, 5: 40}.get(mode, 40)
            mem = (mem & 0xF000) | ((mem + per) & 0x0FFF)
            y += h
        return out

    def run_frame(self, hook=None):
        c = self.cpu
        self.dli_lines = self.parse_dlist()
        lines = self.dl_lines() if self.render_on else {}
        for self.line in range(262):
            if self.line in self.dli_lines and self.nmien & 0x80:
                self.nmi('dli')
            if self.line == 248 and self.nmien & 0x40:
                self.nmi('vbi')
            target = (self.frame * 262 + self.line + 1) * 114
            while self.cycles < target:
                pc = c.pc
                self.cover[pc] = 1
                before = c.processorCycles
                c.step()
                self.cycles += max(2, c.processorCycles - before)
                if hook: hook(self, pc)
            if Y0 <= self.line < Y0 + YH:
                self.draw_line(self.line, lines.get(self.line, (0, 0, 0)))
        self.frame += 1

    # ------------------------------------------------------------ one scan line
    def draw_line(self, s, dl):
        ram = self.ram; g = self.g
        mode, mem, row = dl
        # playfield value per colour clock (0 = BK, 1..3 = PF0..PF2, 4 = PF3, 5 = PF1-luma text)
        pf = np.zeros(XW, np.int16)
        colours = None
        dmactl = self.antic.get(0, 0x3E)
        if mode == 14 and mem is not None:
            b = np.frombuffer(bytes(ram[mem:mem + 40]), np.uint8)
            v = np.stack([(b >> 6) & 3, (b >> 4) & 3, (b >> 2) & 3, b & 3], 1).reshape(-1)
            pf[48 - X0:48 - X0 + 160] = v
        elif mode == 2 and mem is not None:
            chbase = self.antic.get(9, 0xE0) << 8
            chactl = self.antic.get(1, 0)
            bits = np.zeros(320, np.uint8)
            for i in range(40):
                ch = ram[mem + i]; inv = ch & 0x80
                glyph = ram[chbase + (ch & 0x7F) * 8 + row]
                if inv and (chactl & 1): glyph = 0
                elif inv and (chactl & 2): glyph ^= 0xFF
                for k in range(8): bits[i * 8 + k] = (glyph >> (7 - k)) & 1
            colours = bits
            pf[48 - X0:48 - X0 + 160] = 3     # mode 2 background = COLPF2 inside the playfield
        # players and missiles (single-line, PMBASE & $F8)
        pmb = (self.antic.get(7, 0) & 0xF8) << 8
        prior = g[0x1B]
        out = np.zeros((XW, 3), np.uint8)
        pl = np.zeros((4, XW), bool); ms = np.zeros((4, XW), bool)
        if dmactl & 0x08:
            for p in range(4):
                byte = ram[pmb + 0x400 + p * 0x100 + s]
                if not byte: continue
                w = {0: 1, 1: 2, 2: 1, 3: 4}[g[0x08 + p] & 3]
                hp = g[p]
                for k in range(8):
                    if byte & (0x80 >> k):
                        for d in range(w):
                            x = hp + k * w + d - X0
                            if 0 <= x < XW: pl[p, x] = True
        if dmactl & 0x04:
            mb = ram[pmb + 0x300 + s]
            for m in range(4):
                bb = (mb >> (2 * m)) & 3
                if not bb: continue
                w = {0: 1, 1: 2, 2: 1, 3: 4}[(g[0x0C] >> (2 * m)) & 3]
                hp = g[4 + m]
                for k in range(2):
                    if bb & (2 >> k):
                        for d in range(w):
                            x = hp + k * w + d - X0
                            if 0 <= x < XW: ms[m, x] = True
        # collisions (playfield colour bits: value 1->PF0 bit0, 2->PF1 bit1, 3->PF2 bit2)
        pfbits = np.zeros(XW, np.uint8)
        if mode == 14:
            pfbits = np.where(pf == 1, 1, np.where(pf == 2, 2, np.where(pf == 3, 4, 0))).astype(np.uint8)
        for m in range(4):
            if ms[m].any():
                self.coll[m] |= int(np.bitwise_or.reduce(pfbits[ms[m]])) if mode == 14 else 0
                for p in range(4):
                    if (ms[m] & pl[p]).any(): self.coll[8 + m] |= 1 << p
        for p in range(4):
            if pl[p].any():
                if mode == 14: self.coll[4 + p] |= int(np.bitwise_or.reduce(pfbits[pl[p]]))
                for q in range(4):
                    if q != p and (pl[p] & pl[q]).any(): self.coll[12 + p] |= 1 << q
        # colours
        bk = PALETTE[g[0x1A]]
        pfc = [bk, PALETTE[g[0x16]], PALETTE[g[0x17]], PALETTE[g[0x18]], PALETTE[g[0x19]]]
        if mode == 2:
            for x in range(XW):
                out[x] = pfc[3] if pf[x] else bk
            # text: hi-res, two pixels per colour clock; luminance of COLPF1 on COLPF2 hue
            hi = np.zeros((XW * 2, 3), np.uint8)
            hi[:] = np.repeat(out, 2, 0)
            fg = (g[0x18] & 0xF0) | (g[0x17] & 0x0E)
            for i in range(320):
                if colours[i]: hi[(48 - X0) * 2 + i] = PALETTE[fg]
            line = hi
        else:
            for v in range(1, 4):
                out[pf == v] = pfc[v]
            out[pf == 0] = bk
            line = None
        # sprites with PRIOR $31-ish rules: players over playfield; fifth-player missiles as PF3 under PF0-2
        if prior & 0x10:
            mask = ms.any(0) & (pf == 0) if mode == 14 else ms.any(0)
            out[mask] = PALETTE[g[0x19]]
        else:
            for m in range(4):
                out[ms[m]] = PALETTE[g[0x12 + m]]
        for p in (3, 2, 1, 0):
            out[pl[p]] = PALETTE[g[0x12 + p]]
        if prior & 0x20:
            both = pl[0] & pl[1]
            out[both] = PALETTE[g[0x12] | g[0x13]]
            both = pl[2] & pl[3]
            out[both] = PALETTE[g[0x14] | g[0x15]]
        if line is None:
            line = np.repeat(out, 2, 0)
        else:
            # sprites go under the text: draw them, then put the text pixels back on top
            spr = np.repeat(pl.any(0) | ms.any(0), 2)
            line[spr] = np.repeat(out, 2, 0)[spr]
            for i in range(320):
                if colours[i]: line[(48 - X0) * 2 + i] = PALETTE[fg]
        self.frame_rgb[s - Y0] = line

    def image(self):
        from PIL import Image
        return Image.fromarray(self.frame_rgb.copy())
