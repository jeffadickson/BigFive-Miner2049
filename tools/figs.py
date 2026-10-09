"""Figures for the Miner 2049er write-up, drawn from the ROM's own data."""
import os as _os, sys as _sys
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
for _d in ('tools', 'emulator', 'web/tools'):
    if _os.path.join(REPO, _d) not in _sys.path: _sys.path.insert(0, _os.path.join(REPO, _d))

import sys, os, math
from PIL import Image, ImageDraw, ImageFont
from render import atari_rgb

ROM = open(_os.path.join(REPO, 'rom/miner.rom'), 'rb').read()
def rb(a): return ROM[a - 0x8000]
def rw(a): return rb(a) | rb(a + 1) << 8
OUT = _os.path.join(REPO, 'book/fig')
os.makedirs(OUT, exist_ok=True)
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONTB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
MONO = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
def font(sz, bold=False, mono=False): return ImageFont.truetype(MONO if mono else (FONTB if bold else FONT), sz)
INK = (34, 40, 49); GRID = (60, 60, 60); BG = (255, 255, 255); TILE = (12, 12, 16)

def sprite_img(pix, colours, pw=8, ph=5, grid=True):
    """pix: list of rows of colour indices (None = transparent); returns tile image"""
    h = len(pix); w = max(len(r) for r in pix)
    im = Image.new('RGB', (w * pw + 1, h * ph + 1), TILE)
    d = ImageDraw.Draw(im)
    for y, row in enumerate(pix):
        for x, c in enumerate(row):
            if c is None: continue
            d.rectangle([x * pw, y * ph, x * pw + pw - 1, y * ph + ph - 1], fill=colours[c] if isinstance(c, int) else c)
    if grid:
        for x in range(w + 1): d.line([x * pw, 0, x * pw, h * ph], fill=(38, 38, 44))
        for y in range(h + 1): d.line([0, y * ph, w * pw, y * ph], fill=(38, 38, 44))
    return im

def grid_sheet(tiles, labels, cols, title=None, pad=18, lab_h=34, bg=BG):
    tw = max(t.width for t in tiles); th = max(t.height for t in tiles)
    rows = (len(tiles) + cols - 1) // cols
    top = 50 if title else 10
    W = cols * (tw + pad) + pad; H = top + rows * (th + lab_h + pad) + pad
    im = Image.new('RGB', (W, H), bg); d = ImageDraw.Draw(im)
    if title: d.text((pad, 12), title, font=font(24, True), fill=INK)
    for i, (t, lab) in enumerate(zip(tiles, labels)):
        cx = pad + (i % cols) * (tw + pad); cy = top + (i // cols) * (th + lab_h + pad)
        im.paste(t, (cx + (tw - t.width) // 2, cy + (th - t.height)))
        for j, line in enumerate(lab.split('\n')):
            tw2 = d.textlength(line, font=font(15))
            d.text((cx + (tw - tw2) / 2, cy + th + 4 + j * 17), line, font=font(15), fill=INK)
    return im

# ------------------------------------------------------------------ Bob
BOB_COL = {0: 0x8A, 1: 0x3A, 2: 0x0F}
def bob_layers(frame):
    p = rb(0x8247 + frame) | rb(0x8254 + frame) << 8
    rows = {}
    def put(layer, row, byte):
        rows.setdefault(row, [0, 0, 0])[layer] = byte
    for y in range(1, 21): put(0, 0x1E + y, rb(p + y))          # player 0
    for y in range(1, 18): put(1, 0x1E + y, rb(p + 19 + y))     # player 1
    for y in range(1, 18): put(2, 0x24 + y, rb(p + 35 + y))     # player 2
    return rows

def bob_pixels(frame, only=None):
    rows = bob_layers(frame)
    r0, r1 = min(rows), max(rows)
    pix = []
    for r in range(r0, r1 + 1):
        b = rows.get(r, [0, 0, 0]); line = []
        for x in range(8):
            bit = 0x80 >> x
            p0, p1, p2 = [(b[i] & bit) != 0 for i in range(3)]
            if only is not None:
                on = [p0, p1, p2][only]
                line.append(atari_rgb(BOB_COL[only]) if on else None)
                continue
            # PRIOR $31: players in front of the playfield, multicolour (P0|P1 ORed), P0 > P1 > P2
            if p0 and p1: line.append(atari_rgb(BOB_COL[0] | BOB_COL[1]))
            elif p0: line.append(atari_rgb(BOB_COL[0]))
            elif p1: line.append(atari_rgb(BOB_COL[1]))
            elif p2: line.append(atari_rgb(BOB_COL[2]))
            else: line.append(None)
        pix.append(line)
    # trim blank rows
    while pix and all(c is None for c in pix[0]): pix.pop(0)
    while pix and all(c is None for c in pix[-1]): pix.pop()
    return pix

def fig_bob():
    names = ['standing', 'walk right 1', 'walk right 2', 'walk right 3', 'walk left 1', 'walk left 2', 'walk left 3',
             'climb 1', 'climb 2', 'ladder top 1', 'ladder top 2', 'jump right', 'jump left']
    tiles, labs = [], []
    for f in range(1, 13):
        tiles.append(sprite_img(bob_pixels(f), None, 12, 8))
        labs.append('frame %d\n%s' % (f, names[f]))
    grid_sheet(tiles, labs, 6).save(OUT + '/bob_frames.png')
    # layers of frame 1
    tiles = [sprite_img(bob_pixels(1, 0), None, 14, 9), sprite_img(bob_pixels(1, 1), None, 14, 9),
             sprite_img(bob_pixels(1, 2), None, 14, 9), sprite_img(bob_pixels(1), None, 14, 9)]
    labs = ['player 0\nCOLPM0 = $8A', 'player 1\nCOLPM1 = $3A', 'player 2\nCOLPM2 = $0F', 'combined\n(P0|P1 = $BA)']
    grid_sheet(tiles, labs, 4).save(OUT + '/bob_layers.png')

# ------------------------------------------------------------------ mutants
def fig_mutants():
    names = ['right, step 1', 'right, step 2', 'left, step 1', 'left, step 2', 'edible right 1', 'edible right 2',
             'edible left 1', 'edible left 2', 'eaten: "80"', 'eaten: "90"']
    tiles, labs = [], []
    for k in range(10):
        p = 0x8591 + 12 * k
        col = atari_rgb(0xC6 if 4 <= k < 8 else (0x46 if k < 4 else 0x0E))
        pix = [[col if rb(p + y) & (0x80 >> x) else None for x in range(8)] for y in range(10)]
        tiles.append(sprite_img(pix, None, 14, 9)); labs.append('state %d\n%s' % (k, names[k]))
    grid_sheet(tiles, labs, 5).save(OUT + '/mutants.png')

# ------------------------------------------------------------------ items
ITEM_NAMES = {1: '"100"', 2: '"200"', 3: '"300"', 4: '"400"', 5: '"500"', 11: '"1100"', 26: 'BF logo', 33: 'goblet', 34: 'TNT 3 tons', 35: 'TNT 2 tons', 36: 'TNT 1 ton'}
def item_pixels(i, pal):
    p = rw(0x84C5 + 2 * i); w, h, pts = rb(p), rb(p + 1), rb(p + 2); nb = (w - 1) // 4 + 1
    pix = []
    for r in range(h):
        line = []
        for b in range(nb):
            v = rb(p + 3 + r * nb + b)
            for k in range(4):
                c = (v >> (6 - 2 * k)) & 3
                line.append(pal[c] if c else None)
        pix.append(line[:max(w, 1) + (0 if w % 4 == 0 else 4 - w % 4)])
    return pix, w, h, pts

def fig_items():
    pal = [None, atari_rgb(0x46), atari_rgb(0x96), atari_rgb(0xD8)]
    tiles, labs = [], []
    for i in range(1, 37):
        pix, w, h, pts = item_pixels(i, pal)
        tiles.append(sprite_img(pix, None, 10, 6))
        if i <= 5 or i == 11: labs.append('%d\npoints %s' % (i, ITEM_NAMES[i]))
        else: labs.append('%d%s\n%d pts' % (i, (' ' + ITEM_NAMES[i]) if i in ITEM_NAMES else '', pts * 100))
    grid_sheet(tiles, labs, 9).save(OUT + '/items.png')

# ------------------------------------------------------------------ machinery
def fig_machines():
    tiles, labs = [], []
    # transporter booth
    pix = []
    a = 0x9E88
    while rb(a):
        n, pat = rb(a), rb(a + 1); a += 2
        for _ in range(n): pix.append([atari_rgb(0xC6) if pat & (0x80 >> (x // 2)) else None for x in range(16)])
    tiles.append(sprite_img(pix, None, 6, 4)); labs.append('transporter booth\n(BOOTH_SHAPE)')
    # pulverizer head (stored backwards, 3 bytes per line)
    rows = []
    data = [rb(0x9C00 + k) for k in range(18)][::-1]
    pal = [None, atari_rgb(0x46), atari_rgb(0x96), atari_rgb(0xD8)]
    for r in range(6):
        line = []
        for b in range(3):
            v = data[r * 3 + b]
            line += [pal[(v >> (6 - 2 * k)) & 3] for k in range(4)]
        rows.append(line)
    tiles.append(sprite_img(rows, None, 12, 7)); labs.append('pulverizer head\n(PULV_SHAPE)')
    # lift cart + scissor
    rows = []
    sc = [rb(0xA690 + k) for k in range(7)]
    for k in range(2): rows.append([atari_rgb(0x0E)] * 8)
    for k in range(20): rows.append([atari_rgb(0x0E) if sc[k % 7] & (0x80 >> x) else None for x in range(8)])
    for k in range(7): rows.append([atari_rgb(0x0E) if rb(0xA697 + k) & (0x80 >> x) else None for x in range(8)])
    tiles.append(sprite_img(rows, None, 12, 4)); labs.append('lift: platform, scissor\narms and cart (player 3)')
    # cannon: 35 lines (missiles byte, player byte)
    rows = []
    for k in range(35):
        m, p3 = rb(0x9EF3 + 2 * k), rb(0x9EF4 + 2 * k)
        rows.append([atari_rgb(0x04 + 0x06) if (m << 8 | p3) & (0x8000 >> x) else None for x in range(16)])
    tiles.append(sprite_img(rows, None, 7, 4)); labs.append('cannon\n(missiles + player 3)')
    grid_sheet(tiles, labs, 4, pad=60).save(OUT + '/machines.png')

# ------------------------------------------------------------------ jump arc
def fig_jump():
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    ys = [0]; y = 0
    for i in range(48):
        dy = rb(0xBFBD + i) if i < 0x20 else 1
        if dy >= 128: dy -= 256
        y += dy; ys.append(y)
    fig, ax = plt.subplots(figsize=(7.5, 3.0), dpi=160)
    ax.step(range(len(ys)), [-v for v in ys], where='post', color='#3B5B92', lw=2)
    ax.axhline(0, color='#999', lw=0.8)
    ax.set_xlabel('frames since the button was pressed'); ax.set_ylabel('height (lines)')
    ax.set_title('Bob\'s jump (JUMP_ARC)', loc='left', fontsize=11)
    ax.spines[['top', 'right']].set_visible(False); ax.grid(alpha=0.25)
    fig.tight_layout(); fig.savefig(OUT + '/jump_arc.png'); plt.close(fig)

# ------------------------------------------------------------------ mode E byte / girders
def fig_pixels():
    W, H = 1100, 330
    im = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(im)
    d.text((20, 12), 'ANTIC mode E: one byte = four pixels, two bits each', font=font(22, True), fill=INK)
    cols = [(0, 0, 0), atari_rgb(0x46), atari_rgb(0x96), atari_rgb(0xD8)]
    names = ['00 background (COLBK)', '01 colour 1 (COLPF0)', '10 colour 2 (COLPF1)', '11 colour 3 (COLPF2)']
    byte = 0b01101100
    x0, y0, bw = 40, 70, 46
    for b in range(8):
        bit = (byte >> (7 - b)) & 1
        d.rectangle([x0 + b * bw, y0, x0 + b * bw + bw - 2, y0 + 44], outline=INK, width=2)
        d.text((x0 + b * bw + 17, y0 + 8), str(bit), font=font(22, True, True), fill=INK)
        d.text((x0 + b * bw + 14, y0 - 22), 'b%d' % (7 - b), font=font(13), fill=INK)
    for p in range(4):
        v = (byte >> (6 - 2 * p)) & 3
        d.rectangle([x0 + p * 2 * bw, y0 + 60, x0 + p * 2 * bw + 2 * bw - 2, y0 + 120], fill=cols[v], outline=INK)
        d.text((x0 + p * 2 * bw + 12, y0 + 128), 'pixel %d = %d' % (p, v), font=font(14), fill=INK)
    for i in range(4):
        d.rectangle([520, 70 + i * 40, 556, 100 + i * 40], fill=cols[i], outline=INK)
        d.text((568, 76 + i * 40), names[i], font=font(16), fill=INK)
    d.text((40, 250), 'byte address = LINE_LO/HI[y] + x/4      bit pair = x AND 3      PIXEL_MASK = $C0 $30 $0C $03',
           font=font(15, mono=True), fill=INK)
    d.text((40, 278), 'PIXEL_SET colour 1 = $40 $10 $04 $01   colour 2 = $80 $20 $08 $02   colour 3 = PIXEL_MASK',
           font=font(15, mono=True), fill=INK)
    im.save(OUT + '/mode_e.png')

if __name__ == '__main__':
    fig_bob(); fig_mutants(); fig_items(); fig_machines(); fig_jump(); fig_pixels()
    print('ok')
