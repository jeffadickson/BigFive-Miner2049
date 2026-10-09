"""Recursive-descent tracer for the Miner 2049er cartridge ($8000-$BFFF)."""
import os as _os, sys as _sys
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
for _d in ('tools', 'emulator', 'web/tools'):
    if _os.path.join(REPO, _d) not in _sys.path: _sys.path.insert(0, _os.path.join(REPO, _d))

import sys, json
from op6502 import OPS, SIZE

BASE = 0x8000
ROM = open(__import__('os').environ.get('ROM',_os.path.join(REPO, 'rom/miner.rom')), 'rb').read()

def rb(a): return ROM[a - BASE]
def rw(a): return rb(a) | rb(a + 1) << 8
def inrom(a): return BASE <= a < BASE + len(ROM)

def decode(a):
    op = rb(a)
    if op not in OPS: return None
    mn, md = OPS[op]
    n = SIZE[md]
    if a + n > BASE + len(ROM): return None
    if n == 1: v = None
    elif n == 2: v = rb(a + 1)
    else: v = rw(a + 1)
    if md == 'rel':
        v = (a + 2 + (v - 256 if v >= 128 else v)) & 0xFFFF
    return mn, md, n, v

def trace(entries, extra_stops=()):
    code = {}          # addr -> (mn, md, n, v)
    refs = {}          # target -> set of (from, kind)
    work = list(entries)
    bad = []
    while work:
        a = work.pop()
        while inrom(a) and a not in code:
            d = decode(a)
            if d is None:
                bad.append(a); break
            code[a] = d
            mn, md, n, v = d
            if md == 'rel':
                refs.setdefault(v, set()).add((a, 'br')); work.append(v)
            elif mn == 'JSR':
                refs.setdefault(v, set()).add((a, 'jsr')); work.append(v)
            elif mn == 'JMP' and md == 'abs':
                refs.setdefault(v, set()).add((a, 'jmp')); work.append(v); break
            elif md in ('abs', 'absx', 'absy', 'ind'):
                refs.setdefault(v, set()).add((a, 'data'))
            if mn in ('RTS', 'RTI', 'BRK') or (mn == 'JMP'):
                break
            if a in extra_stops: break
            a += n
    return code, refs, bad

if __name__ == '__main__':
    ents = [int(x, 16) for x in sys.argv[1:]] or [0xA228, 0xA1B5]
    code, refs, bad = trace(ents)
    print(len(code), 'instrs', sum(c[2] for c in code.values()), 'bytes; bad', [hex(b) for b in bad])
