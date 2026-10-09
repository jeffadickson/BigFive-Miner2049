import os as _os, sys as _sys
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
for _d in ('tools', 'emulator', 'web/tools'):
    if _os.path.join(REPO, _d) not in _sys.path: _sys.path.insert(0, _os.path.join(REPO, _d))

import sys, os, json, shutil
from emu2 import Atari2
from movie import encode
OUT = _os.path.join(REPO, 'web/out/data')
FR = _os.path.join(REPO, 'shots/hframes')
REC0 = 0x978C
REC = [(None, None)]
ROM = open(_os.path.join(REPO, 'rom/miner.rom'), 'rb').read()
rec = [(ROM[a - 0x8000], ROM[a + 1 - 0x8000]) for a in range(0x978C, 0x9818, 2)]
cum = [0]
for v, n in rec: cum.append(cum[-1] + n)

def save(at, d, k):
    at.image().save('%s/%s/f%05d.png' % (FR, d, k))

def run(which):
    at = Atari2()
    os.makedirs(FR + '/' + which, exist_ok=True)
    for f in os.listdir(FR + '/' + which): os.remove(FR + '/' + which + '/' + f)
    meta = {'gf': []}
    if which == 'credits':
        k = 0
        for fr in range(3300):
            at.run_frame()
            if fr % 2 == 0: save(at, which, k); k += 1
        meta.update(step=2, first=0)
    elif which == 'demo':
        at.render_on = False
        fr = 0
        while True:   # until the high-score screen
            at.run_frame(); fr += 1
            if (at.ram[0x222] | at.ram[0x223] << 8) == 0x94AD: break
        for i in range(10): at.run_frame()
        at.ram[0xC8] = 0           # T_DEMOSEC: start the demo now
        while not (at.ram[0xB7] == 1 and at.ram[0xE2] != 0 and (at.ram[0x222] | at.ram[0x223] << 8) == 0xBBB0):
            at.run_frame()
        at.render_on = True
        k = 0; n = 0
        while True:
            at.run_frame(); n += 1
            p = at.ram[0xE1] | at.ram[0xE2] << 8
            if at.ram[0xE2] == 0 or at.ram[0xB7] != 1 or n > 3200: break
            idx = (p - REC0) // 2
            gf = cum[idx] + (rec[idx][1] - at.ram[0xDF]) if 0 <= idx < len(rec) else -1
            if n % 2 == 0:
                save(at, which, k); meta['gf'].append(gf); k += 1
        meta.update(step=2, first=0, end_reason='station %d demo_hi %d frames %d' % (at.ram[0xB7], at.ram[0xE2], n))
    files = sorted(os.listdir(FR + '/' + which))
    info, size = encode([FR + '/' + which + '/' + f for f in files], OUT + '/movie_%s.bin' % which, fps=30)
    info.update(meta)
    import base64
    info['poster'] = 'data:image/png;base64,' + base64.b64encode(open(FR + '/' + which + '/' + files[min(len(files) - 1, 40)], 'rb').read()).decode()
    json.dump(info, open(OUT + '/movie_%s.json' % which, 'w'))
    print(which, info['n'], len(info['pal']), size, meta.get('end_reason'))

if __name__ == '__main__':
    run(sys.argv[1])
