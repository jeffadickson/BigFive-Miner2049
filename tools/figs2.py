"""Annotated screenshots and timing diagrams."""
import os as _os, sys as _sys
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
for _d in ('tools', 'emulator', 'web/tools'):
    if _os.path.join(REPO, _d) not in _sys.path: _sys.path.insert(0, _os.path.join(REPO, _d))

import sys, os, pickle
from PIL import Image, ImageDraw
from figs import font, INK, OUT
from render import atari_rgb

SH = _os.path.join(REPO, 'shots/')

def scaled(path, s=3):
    im = Image.open(path).convert('RGB')
    return im.resize((im.width * s, im.height * s), Image.NEAREST)

def fig_bands():
    s = 3
    im = scaled(SH + 'st_1.png', s)
    W = im.width + 430
    out = Image.new('RGB', (W, im.height + 20), (255, 255, 255))
    out.paste(im, (10, 10))
    d = ImageDraw.Draw(out)
    # band boundaries: DLI at the end of the status line and of bitmap rows 46, 93, 140
    bounds = [(16, 'status line (ANTIC mode 2, 40 chars at $20D8)'), (24, 'DLI 1  (end of status line)'),
              (24 + 47, 'DLI 2  (bitmap line 46)'), (24 + 94, 'DLI 3  (bitmap line 93)'), (24 + 141, 'DLI 4  (bitmap line 140)'),
              (24 + 184, 'end of the 184-line bitmap')]
    cols = [(230, 120, 40), (40, 150, 230), (40, 150, 230), (40, 150, 230), (40, 150, 230), (230, 120, 40)]
    for (y, lab), c in zip(bounds, cols):
        Y = 10 + y * s
        for x in range(10, 10 + im.width, 12): d.line([x, Y, x + 6, Y], fill=c, width=2)
        d.line([10 + im.width, Y, 10 + im.width + 18, Y], fill=c, width=2)
        d.text((10 + im.width + 24, Y - 10), lab, font=font(17), fill=INK)
    bands = [(24, 71, 'band A: mutants 0 + 1'), (71, 118, 'band B: mutants 2 + 3'), (118, 165, 'band C: mutants 4 + 5'),
             (165, 208, 'band D: mutants 6 + 7  (cannon on st. 10)')]
    for y0, y1, lab in bands:
        Y = 10 + (y0 + y1) / 2 * s
        d.text((10 + im.width + 40, Y - 9), lab, font=font(16), fill=(90, 90, 90))
    out.save(OUT + '/screen_bands.png')

def fig_title_lights():
    s = 3
    im = scaled(SH + 'hs1.png', s)
    out = Image.new('RGB', (im.width + 20, im.height + 150), (255, 255, 255))
    out.paste(im, (10, 10))
    d = ImageDraw.Draw(out)
    def box(x0, y0, x1, y1, c, lab, ly):
        d.rectangle([10 + x0 * s, 10 + y0 * s, 10 + x1 * s, 10 + y1 * s], outline=c, width=3)
        d.text((10 + x0 * s, 10 + im.height + ly), lab, font=font(17, True), fill=c)
    # top row (approximate positions measured from the screenshot)
    box(4, 17, 127, 35, (240, 170, 30), 'playfield, colours set by the kernel (left 4)', 10)
    box(130, 17, 194, 35, (60, 200, 90), 'players 1 + 2', 38)
    box(197, 17, 318, 35, (240, 170, 30), 'playfield, kernel (right 4)', 66)
    box(4, 36, 20, 196, (90, 160, 250), 'left column: player 0, recoloured by a DLI on every line', 94)
    box(316, 36, 332, 196, (90, 160, 250), '', 94)
    d.text((10 + 316 * s - 330, 10 + im.height + 122), 'right column: player 3', font=font(17, True), fill=(90, 160, 250))
    out.save(OUT + '/title_lights.png')

def fig_kernel():
    W, H = 1150, 280
    im = Image.new('RGB', (W, H), (255, 255, 255)); d = ImageDraw.Draw(im)
    d.text((20, 10), 'TITLE_KERNEL: one pass plus ANTIC\'s DMA is meant to fill one scan line (114 cycles)', font=font(20, True), fill=INK)
    x0, y0, cyc = 40, 80, 9.0
    segs = [('delay\n3/4/5', 4, (200, 200, 200)), ('COLPF0', 6, (240, 170, 30)), ('COLPF1', 6, (240, 170, 30)), ('COLPF2', 6, (240, 170, 30)),
            ('COLPF3', 6, (240, 170, 30)), ('COLPF0', 6, (60, 170, 240)), ('COLPF1', 6, (60, 170, 240)), ('COLPF2', 6, (60, 170, 240)),
            ('COLPF3', 6, (60, 170, 240)), ('pad\n6+6+6', 18, (220, 220, 220)), ('delay', 4, (200, 200, 200)), ('DEX\nBEQ\nJMP', 7, (230, 230, 230))]
    x = x0
    for lab, n, c in segs:
        w = n * cyc
        d.rectangle([x, y0, x + w, y0 + 70], fill=c, outline=INK)
        for j, line in enumerate(lab.split('\n')):
            tw = d.textlength(line, font=font(13))
            d.text((x + (w - tw) / 2, y0 + 8 + j * 16), line, font=font(13), fill=INK)
        x += w
    d.text((x0, y0 + 85), 'LDA #colour / STA COLPFn = 2 + 4 cycles each.  Orange: colours for the left four lights;  blue: the right four,',
           font=font(15), fill=INK)
    d.text((x0, y0 + 108), 'written while the beam is half way across the row.  The "LDA #" operands and the STA high bytes are patched',
           font=font(15), fill=INK)
    d.text((x0, y0 + 131), 'every frame (high bytes by KERNEL_COLS_TOP); two delay opcodes are patched to CPX zp (3), CMP zp,X (4) or ASL zp (5 cycles) so the colour',
           font=font(15), fill=INK)
    d.text((x0, y0 + 154), 'changes move 6, 8 or 10 colour clocks to follow HSCROL.  No WSYNC in the loop: the timing is counted.',
           font=font(15), fill=INK)
    im.save(OUT + '/kernel_timing.png')

def fig_girders():
    ram = pickle.load(open(_os.path.join(REPO, 'shots/s1_demo.ram'), 'rb'))
    cols = [(0, 0, 0), atari_rgb(0x46), atari_rgb(0x96), atari_rgb(0xD8)]
    # find a region with both claimed and unclaimed sections: Bob claimed the lower girders
    y0, y1, x0, x1 = 139, 150, 52, 108
    s = 9; pw, ph = s * 2, s
    im = Image.new('RGB', ((x1 - x0) * pw // 2 + 1, (y1 - y0) * ph + 1), (0, 0, 0))
    d = ImageDraw.Draw(im)
    for y in range(y0, y1):
        for x in range(x0, x1):
            b = ram[0x2100 + 40 * y + x // 4]
            v = (b >> (6 - 2 * (x % 4))) & 3
            X = (x - x0) * pw // 2; Y = (y - y0) * ph
            d.rectangle([X, Y, X + pw // 2 - 1, Y + ph - 1], fill=cols[v])
    for x in range(x0, x1, 4):
        X = (x - x0) * pw // 2
        d.line([X, 0, X, im.height], fill=(45, 45, 45))
    im.save(OUT + '/girders_zoom.png')

if __name__ == '__main__':
    fig_bands(); fig_title_lights(); fig_kernel(); fig_girders()
    print('ok')
