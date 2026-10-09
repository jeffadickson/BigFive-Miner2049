"""Render the game's bitmap ($2100, 184 lines x 160 px, ANTIC mode E) from emulator RAM."""
import os as _os, sys as _sys
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
for _d in ('tools', 'emulator', 'web/tools'):
    if _os.path.join(REPO, _d) not in _sys.path: _sys.path.insert(0, _os.path.join(REPO, _d))

import sys, os
from PIL import Image
# NTSC Atari palette (approximate, generated)
import colorsys, math
def atari_rgb(c):
    """Approximate NTSC Atari colour (fitted to the emulator's default palette)."""
    hue = c >> 4; lum = (c & 0x0F) >> 1
    y = lum / 7.0 * 0.8
    if hue == 0:
        v = int(y * 255 + 0.5); return (v, v, v)
    ang = math.radians(312 + (hue - 1) * 26)
    i = 0.15 * math.cos(ang); q = 0.15 * math.sin(ang)
    r = y + 0.956 * i + 0.621 * q; g = y - 0.272 * i - 0.647 * q; b = y - 1.106 * i + 1.703 * q
    return tuple(max(0, min(255, int(v * 255))) for v in (r, g, b))

def render_bitmap(ram, colours=None, scale=3):
    if colours is None:
        colours = [ram[0x8A], ram[0x8B], ram[0x8C], ram[0x8D]]
    pal = [atari_rgb(c) for c in colours]
    img = Image.new('RGB', (160, 184))
    px = img.load()
    for y in range(184):
        base = 0x2100 + 40 * y
        for xb in range(40):
            b = ram[base + xb]
            for k in range(4):
                v = (b >> (6 - 2 * k)) & 3
                px[xb * 4 + k, y] = pal[v]
    return img.resize((160 * 2 * scale, 184 * scale), Image.NEAREST)
