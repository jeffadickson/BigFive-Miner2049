"""Quick raw listing: traced code as instructions, the rest as hex rows. Usage: raw.py [entries...]"""
import os as _os, sys as _sys
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
for _d in ('tools', 'emulator', 'web/tools'):
    if _os.path.join(REPO, _d) not in _sys.path: _sys.path.insert(0, _os.path.join(REPO, _d))

import sys, os
from trace import trace, rb, decode, BASE, ROM
from hw import hwname, zpptr, OSVEC

FMT = {'imp': '', 'acc': 'A', 'imm': '#$%02X', 'zp': '$%02X', 'zpx': '$%02X,X', 'zpy': '$%02X,Y',
       'abs': '$%04X', 'absx': '$%04X,X', 'absy': '$%04X,Y', 'ind': '($%04X)', 'indx': '($%02X,X)',
       'indy': '($%02X),Y', 'rel': '$%04X'}

def opnd(md, v):
    f = FMT[md]
    return f % v if '%' in f else f

def main():
    ents = [int(x, 16) for x in open('entries.txt').read().split()] if os.path.exists('entries.txt') else []
    code, refs, bad = trace(ents)
    out = []
    a = BASE
    while a < BASE + len(ROM):
        if a in refs:
            kinds = sorted({k for _, k in refs[a]})
            out.append('L%04X:   ; refs %s from %s' % (a, ','.join(kinds), ' '.join('%04X' % f for f, _ in sorted(refs[a])[:8])))
        if a in code:
            mn, md, n, v = code[a]
            w = mn in ('STA','STX','STY','INC','DEC','ASL','LSR','ROL','ROR')
            c = ''
            if md in ('abs','absx','absy') and v is not None:
                c = hwname(v, w) or OSVEC.get(v) or ''
            if md in ('indx','indy'):
                c = zpptr(v, w) or ''
                if c: c = '->' + c
            out.append('%04X  %-9s %s %-10s %s' % (a, ' '.join('%02X' % rb(a + i) for i in range(n)), mn, opnd(md, v), ('; '+c) if c else ''))
            if mn in ('RTS', 'RTI', 'JMP'): out.append('')
            a += n
        else:
            s = a
            row = []
            while a < BASE + len(ROM) and a not in code and len(row) < 16:
                row.append(rb(a)); a += 1
                if a in refs: break
            out.append('%04X  .byte %s' % (s, ','.join('$%02X' % b for b in row)))
    open('raw.lst', 'w').write('\n'.join(out) + '\n')
    tot = sum(c[2] for c in code.values())
    print('code bytes', tot, 'bad', [hex(b) for b in bad])

main()
