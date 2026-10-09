"""Generate the commented ca65 source for Miner 2049er from the ROM plus annotation files.

Annotation directives (one per line, files read in sorted order from annot/):
  = NAME value [; comment]       equate (value $hex or decimal)
  L addr NAME                    label
  C addr text                    inline comment on the line that starts at addr
  H addr                         header block; following lines beginning with '|' form the block
  D start end kind [n]           data formatting: kind = byte|text|word|dlist|gfx|gfx2|tbl ; n = bytes per row
  X addr                         extra code entry point
  R start end base               relocated block: bytes at start..end execute at base
  N start end                    force data (never code) in range
  # ...                          ignored
"""
import os as _os, sys as _sys
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
for _d in ('tools', 'emulator', 'web/tools'):
    if _os.path.join(REPO, _d) not in _sys.path: _sys.path.insert(0, _os.path.join(REPO, _d))

import sys, os, re, glob
from op6502 import OPS, SIZE
from hw import hwname, zpptr

ROM = open(os.environ.get('ROM', _os.path.join(REPO, 'rom/miner.rom')), 'rb').read()
BASE = 0x8000
END = BASE + len(ROM)
def rb(a): return ROM[a - BASE]
def rw(a): return rb(a) | rb(a + 1) << 8

# ---------------------------------------------------------------- annotations
equ = {}          # name -> (value, comment)
equ_by_val = {}   # value -> name (zero page / RAM / hw), first wins
labels = {}       # addr -> name
comments = {}     # addr -> text
headers = {}      # addr -> [lines]
datafmt = []      # (start, end, kind, n)
entries = []
relocs = []       # (start, end, base)
forcedata = []
overrides = {}   # addr -> operand text
summaries = {}   # addr -> one-line description used for calls
scoped = []      # (start, end, value, name): zp alias used only for code in [start,end]

def num(s):
    s = s.strip()
    if s.startswith('$'): return int(s[1:], 16)
    if s.startswith('0x'): return int(s, 16)
    if re.fullmatch(r'[0-9A-Fa-f]{4}', s): return int(s, 16)
    return int(s)

def load(path):
    cur = None
    for raw in open(path):
        line = raw.rstrip('\n')
        if line.startswith('|'):
            if cur is None: raise SystemExit('stray | in %s: %s' % (path, line))
            headers[cur].append(line[1:].rstrip()[1:] if line[1:2] == ' ' else line[1:].rstrip())
            continue
        cur = None
        s = line.strip()
        if not s or s.startswith('#'): continue
        k, rest = s[0], s[1:].strip()
        if k == '=':
            name, rest2 = rest.split(None, 1)
            if ';' in rest2: v, c = rest2.split(';', 1)
            else: v, c = rest2, ''
            val = num(v)
            equ[name] = (val, c.strip())
            equ_by_val.setdefault(val, name)
        elif k == 'L':
            a, name = rest.split(None, 1)
            labels[num(a)] = name.strip()
        elif k == 'C':
            a, t = (rest.split(None, 1) + [''])[:2]
            a = num(a)
            comments[a] = (comments[a] + '; ' + t) if a in comments else t
        elif k == 'H':
            cur = num(rest.split()[0])
            headers.setdefault(cur, [])
            if headers[cur]: headers[cur].append('')
        elif k == 'D':
            p = rest.split()
            datafmt.append((num(p[0]), num(p[1]), p[2], int(p[3]) if len(p) > 3 else 0))
        elif k == 'X':
            for t in rest.split(): entries.append(num(t))
        elif k == 'R':
            p = rest.split(); relocs.append((num(p[0]), num(p[1]), num(p[2])))
        elif k == 'S':
            p = rest.split(); scoped.append((num(p[0]), num(p[1]), num(p[2]), p[3]))
        elif k == 'Y':
            a, t = rest.split(None, 1)
            summaries[num(a)] = t.strip()
        elif k == 'O':
            a, t = rest.split(None, 1)
            overrides[num(a)] = t.strip()
        elif k == 'N':
            p = rest.split(); forcedata.append((num(p[0]), num(p[1])))
        else:
            raise SystemExit('bad directive in %s: %s' % (path, line))

for f in sorted(glob.glob(os.path.join(REPO, 'src', 'annot', '*.txt'))):
    load(f)

# ---------------------------------------------------------------- tracing
def decode_at(a, mem_base=0):
    """decode instruction from ROM address a; mem_base offset converts to run address"""
    op = rb(a)
    if op not in OPS: return None
    mn, md = OPS[op]
    n = SIZE[md]
    if a + n > END: return None
    v = None
    if n == 2: v = rb(a + 1)
    elif n == 3: v = rw(a + 1)
    if md == 'rel':
        run = a + mem_base
        v = (run + 2 + (v - 256 if v >= 128 else v)) & 0xFFFF
    return mn, md, n, v

def reloc_of(a):
    for s, e, b in relocs:
        if s <= a <= e: return s, e, b
    return None

def isforced(a):
    return any(s <= a <= e for s, e in forcedata)

code = {}
work = list(entries)
bad = []
while work:
    a = work.pop()
    while BASE <= a < END and a not in code and not isforced(a):
        r = reloc_of(a)
        off = (r[2] - r[0]) if r else 0
        d = decode_at(a, off)
        if d is None: bad.append(a); break
        code[a] = d
        mn, md, n, v = d
        def rom_of(t):
            if r and r[2] <= t <= r[2] + (r[1] - r[0]): return t - off
            return t
        if md == 'rel': work.append(rom_of(v))
        elif mn == 'JSR': work.append(rom_of(v))
        elif mn == 'JMP' and md == 'abs': work.append(rom_of(v)); break
        if mn in ('RTS', 'RTI', 'BRK', 'JMP'): break
        a += n
        if r and a > r[1]: break

# ---------------------------------------------------------------- label resolution
codestart = set(code)
def runaddr(a):
    r = reloc_of(a)
    return a + (r[2] - r[0]) if r else a

# every branch/jump target in ROM gets a label
auto = {}
for a, (mn, md, n, v) in code.items():
    r = reloc_of(a)
    if md == 'rel' or (mn in ('JSR', 'JMP') and md == 'abs'):
        t = v
        if r and r[2] <= t <= r[2] + r[1] - r[0]: t = t - (r[2] - r[0])
        if BASE <= t < END and t not in labels: auto[t] = 'L%04X' % t
for t, nm in auto.items(): labels.setdefault(t, nm)
_seen = {}
for a_, nm in labels.items():
    if nm in _seen: raise SystemExit('duplicate label %s at %04X and %04X' % (nm, _seen[nm], a_))
    _seen[nm] = a_

# run-address -> label map (for relocated code, label value is the run address)
runlabel = {}
for a, nm in labels.items():
    runlabel[runaddr(a)] = nm

def sym_abs(v, ctx_reloc):
    """symbolic expression for absolute operand value v"""
    if v in runlabel and (BASE <= v < END or (ctx_reloc and v in runlabel)):
        return runlabel[v]
    for r in relocs:
        if r[2] <= v <= r[2] + r[1] - r[0]:
            if v in runlabel: return runlabel[v]
            # nearest label inside relocated block
            best = max((x for x in runlabel if r[2] <= x <= v), default=None)
            if best is not None: return '%s+%d' % (runlabel[best], v - best)
    if BASE <= v < END:
        # nearest preceding label within 48 bytes, else following within 4
        best = max((x for x in labels if x <= v and v - x <= 48 and not reloc_of(x)), default=None)
        nxt = min((x for x in labels if x > v and x - v <= 4 and not reloc_of(x)), default=None)
        if nxt is not None and (best is None or nxt - v < v - best):
            return '%s-%d' % (labels[nxt], nxt - v)
        if best is not None:
            return labels[best] if best == v else '%s+%d' % (labels[best], v - best)
        return '$%04X' % v
    if v in equ_by_val and v >= 0x100: return equ_by_val[v]
    # RAM equate + offset (tables)
    best = max((val for val in equ_by_val if 0x100 <= val <= v and v - val < 0x40 and val < 0x8000), default=None)
    if best is not None and v < 0xD000:
        return '%s+%d' % (equ_by_val[best], v - best) if best != v else equ_by_val[best]
    return '$%04X' % v

CUR = [0]
SCOPED_NAMES = set(nm for _s, _e, _v, nm in scoped)
for _v in list(equ_by_val):
    if equ_by_val[_v] in SCOPED_NAMES:
        # find a default (unscoped) name for this value, else drop it
        alt = [n for n, (vv, c) in equ.items() if vv == _v and n not in SCOPED_NAMES]
        if alt: equ_by_val[_v] = alt[0]
        else: del equ_by_val[_v]
def sym_zp(v):
    for s_, e_, val, nm in scoped:
        if s_ <= CUR[0] <= e_:
            if val == v: return nm
            if val == v - 1 and nm + '+1' and (val, nm): pass
    for s_, e_, val, nm in scoped:
        if s_ <= CUR[0] <= e_ and val == v - 1 and not any(s2 <= CUR[0] <= e2 and v2 == v for s2, e2, v2, n2 in scoped):
            return nm + '+1'
    if v in equ_by_val: return equ_by_val[v]
    best = max((val for val in equ_by_val if val <= v and v - val <= 1 and val < 0x100), default=None)
    if best is not None and best != v:
        return '%s+%d' % (equ_by_val[best], v - best)
    return '$%02X' % v

def operand(a, mn, md, v):
    CUR[0] = a
    if a in overrides: return overrides[a]
    r = reloc_of(a)
    if md == 'imp': return ''
    if md == 'acc': return 'a'
    if md == 'imm': return '#$%02X' % v
    if md in ('zp', 'zpx', 'zpy'):
        s = sym_zp(v)
        return s + {'zp': '', 'zpx': ',x', 'zpy': ',y'}[md]
    if md == 'indx': return '(%s,x)' % sym_zp(v)
    if md == 'indy': return '(%s),y' % sym_zp(v)
    if md == 'rel':
        t = v
        return runlabel.get(t, '$%04X' % t)
    if md == 'ind': return '(%s)' % sym_abs(v, r)
    s = sym_abs(v, r)
    if v < 0x100: s = 'a:' + s
    return s + {'abs': '', 'absx': ',x', 'absy': ',y'}[md]


# ---------------------------------------------------------------- automatic comments
SUMMARY = {}
for _a, _lines in headers.items():
    if _a < 0 or not _lines: continue
    first = _lines[0].strip()
    if ' - ' in first:
        nm, txt = first.split(' - ', 1)
        txt = txt.strip()
        # take the first sentence
        for stop in ('. ', ': '):
            if stop in txt: txt = txt.split(stop)[0]
        txt = txt.rstrip('.')
        SUMMARY[_a] = txt[:70]
SUMMARY.update(summaries)
from hw import zpptr as _zpptr
def auto_comment(a, mn, md, v):
    r = reloc_of(a)
    if mn in ('JSR', 'JMP') and md == 'abs':
        t = v
        if r and r[2] <= t <= r[2] + r[1] - r[0]: t -= (r[2] - r[0])
        if t in SUMMARY:
            return SUMMARY[t]
    if md == 'indy':
        w = mn in ('STA',)
        n = _zpptr(v, w)
        if n:
            return ('%s = A' % n) if w else ({'LDA': 'A = %s', 'ORA': 'A |= %s', 'AND': 'A &= %s', 'CMP': 'compare with %s'}.get(mn, '%s') % n)
    return ''


# ---------------------------------------------------------------- pseudo-code comments
def _sym(a, mn, md, v):
    """operand text for pseudo-code"""
    if md == 'imm': return '#$%02X' % v
    o = operand(a, mn, md, v)
    return o
def _plain(a):
    """A readable name for a memory operand of the instruction at a, or None"""
    mn, md, n, v = code[a]
    if md in ('zp', 'abs'):
        return operand(a, mn, md, v).replace('a:', '')
    if md in ('zpx', 'absx'): return operand(a, mn, md, v).replace('a:', '').replace(',x', '[X]')
    if md in ('zpy', 'absy'): return operand(a, mn, md, v).replace('a:', '').replace(',y', '[Y]')
    if md == 'imm': return '$%02X' % v if v > 9 else str(v)
    if md == 'indy':
        hwn = _zpptr(v, mn.startswith('ST'))
        if hwn: return hwn
        return '(%s)[Y]' % sym_zp(v)
    return None
BR = {'BEQ': '==', 'BNE': '<>', 'BCC': '<', 'BCS': '>=', 'BMI': '< 0 (bit 7)', 'BPL': '>= 0 (bit 7)'}
PSEUDO = {}
def build_pseudo():
    addrs = sorted(code)
    nxt = {}
    for i, a in enumerate(addrs[:-1]):
        if addrs[i + 1] == a + code[a][2]: nxt[a] = addrs[i + 1]
    def ins(a): return code.get(a)
    for a in addrs:
        mn, md, n, v = code[a]
        b = nxt.get(a); c = nxt.get(b) if b else None; d = nxt.get(c) if c else None
        # load / op / store sequences
        if mn == 'LDA' and b and code[b][0] == 'STA' and _plain(a) and _plain(b):
            if b not in labels:
                PSEUDO.setdefault(a, '%s = %s' % (_plain(b), _plain(a)))
            continue
        if mn == 'LDA' and b and c and d and code[b][0] in ('CLC', 'SEC') and code[c][0] in ('ADC', 'SBC') and code[d][0] == 'STA' \
                and _plain(a) and _plain(c) and _plain(d) and not any(x in labels for x in (b, c, d)):
            op = '+' if code[c][0] == 'ADC' else '-'
            if (code[b][0] == 'CLC') == (op == '+'):
                PSEUDO.setdefault(a, '%s = %s %s %s' % (_plain(d), _plain(a), op, _plain(c)))
            continue
        if mn in ('CMP', 'CPX', 'CPY') and b and code[b][0] in BR and b not in labels and _plain(a):
            reg = {'CMP': 'A', 'CPX': 'X', 'CPY': 'Y'}[mn]
            br = code[b][0]
            if br in ('BMI', 'BPL'): continue
            PSEUDO.setdefault(a, 'if %s %s %s goto %s' % (reg, BR[br], _plain(a), runlabel.get(code[b][3], '$%04X' % code[b][3])))
            continue
        if mn in ('LDA', 'LDX', 'LDY') and md != 'imm' and b and code[b][0] in ('BEQ', 'BNE', 'BMI', 'BPL') and b not in labels and _plain(a):
            br = code[b][0]
            cond = {'BEQ': '== 0', 'BNE': '<> 0', 'BMI': 'bit 7 set', 'BPL': 'bit 7 clear'}[br]
            PSEUDO.setdefault(a, 'if %s %s goto %s' % (_plain(a), cond, runlabel.get(code[b][3], '$%04X' % code[b][3])))
            continue
        if mn in ('DEC', 'INC') and b and code[b][0] in ('BNE', 'BEQ') and b not in labels and _plain(a):
            br = code[b][0]
            PSEUDO.setdefault(a, '%s %s 1, %s' % (_plain(a), '-=' if mn == 'DEC' else '+=', ('until 0' if br == 'BNE' else 'goto %s if 0' % runlabel.get(code[b][3], '?'))))
            continue
        if mn in ('DEX', 'DEY') and b and code[b][0] == 'BNE' and b not in labels:
            PSEUDO.setdefault(a, 'loop until %s = 0' % mn[2])
            continue
        if mn == 'AND' and md == 'imm' and b and code[b][0] in ('BEQ', 'BNE') and b not in labels:
            PSEUDO.setdefault(a, 'test bits $%02X' % v)
            continue

# ---------------------------------------------------------------- output
def scr(b):
    """ANTIC internal code -> printable"""
    inv = b & 0x80
    b &= 0x7F
    if b < 0x40: c = chr(b + 0x20)
    elif b < 0x60: c = '.'
    else: c = chr(b)
    return c

build_pseudo()
out = []
W = 40   # comment column
def emit(lbl, body, cmt=''):
    s = ''
    if lbl:
        if len(lbl) >= 15:
            out.append(lbl + ':'); s = ' ' * 16
        else:
            s = (lbl + ':').ljust(16)
    else:
        s = ' ' * 16
    s += body
    if cmt:
        base = s.ljust(W)
        room = 116 - len(base) - 2
        words = cmt.split(' ')
        lines = ['']
        for wd in words:
            if lines[-1] and len(lines[-1]) + 1 + len(wd) > room:
                lines.append(wd)
            else:
                lines[-1] = (lines[-1] + ' ' + wd) if lines[-1] else wd
        s = base + '; ' + lines[0]
        for extra in lines[1:]:
            out.append(s.rstrip())
            s = ' ' * len(base) + ';   ' + extra
    out.append(s.rstrip())

def fmt_of(a):
    for s, e, k, n in datafmt:
        if s <= a <= e: return s, e, k, n
    return None

out.append('; ' + '=' * 76)
for line in headers.get(-1, []): out.append(('; ' + line).rstrip())
out.append('; ' + '=' * 76)
out.append('')
out.append('        .setcpu "6502"')
out.append('')
# equates
groups = {}
for name, (val, c) in equ.items():
    groups.setdefault(c.split(':')[0] if c.startswith('[') else '', []).append(name)
for name, (val, c) in sorted(equ.items(), key=lambda kv: (kv[1][0] >= 0x100, kv[1][0])):
    if name in headers: pass
    line = '%-15s = %s' % (name, ('$%02X' % val) if val < 0x100 else ('$%04X' % val))
    if c:
        words = c.split(' '); parts = ['']
        for wd in words:
            if parts[-1] and len(parts[-1]) + 1 + len(wd) > 116 - W - 2: parts.append(wd)
            else: parts[-1] = (parts[-1] + ' ' + wd) if parts[-1] else wd
        line = line.ljust(W) + '; ' + parts[0]
        for p_ in parts[1:]:
            out.append(line); line = ' ' * W + ';   ' + p_
    out.append(line)
out.append('')
out.append('        .org $8000')
out.append('')

a = BASE
cur_reloc = None
while a < END:
    r = reloc_of(a)
    if r and a == r[0]:
        out.append('')
        out.append('        .org $%04X                      ; --- block runs in RAM at $%04X (copied there from ROM $%04X) ---' % (r[2], r[2], r[0]))
        cur_reloc = r
    if a in headers:
        out.append('')
        out.append(';' + '-' * 77)
        for line in headers[a]:
            if not line: out.append(';'); continue
            full = ';  ' + line
            while len(full) > 116:
                cut = full.rfind(' ', 0, 116)
                out.append(full[:cut].rstrip())
                ind = len(line) - len(line.lstrip())
                full = ';  ' + ' ' * ind + full[cut + 1:]
            out.append(full.rstrip())
        out.append(';' + '-' * 77)
    lbl = labels.get(a)
    if a in code:
        mn, md, n, v = code[a]
        body = '%-4s%s' % (mn.lower(), operand(a, mn, md, v))
        cm = comments.get(a, '')
        if not cm:
            cm = auto_comment(a, mn, md, v) or PSEUDO.get(a, '')
        emit(lbl, body, cm)
        a += n
    else:
        f = fmt_of(a)
        if f: s, e, kind, per = f
        else: s, e, kind, per = a, END - 1, 'byte', 16
        # run until next label/code/format boundary
        stop = a
        limit = e
        per = per or 16
        while stop <= limit and stop not in code and (stop == a or (stop not in labels and stop not in headers)):
            stop += 1
            if stop - a >= per: break
            nf = fmt_of(stop)
            if nf != f: break
            if any(rs == stop for rs, re_, rbase in relocs): break
        if kind == 'dlist':
            # one display-list instruction per line
            ins = rb(a); mode = ins & 15
            n = 3 if (mode == 1 or (mode and ins & 0x40)) else 1
            n = min(n, e - a + 1)
            stop = a + n
            if mode == 0: d = '%d blank line%s' % (((ins >> 4) & 7) + 1, 's' if (ins >> 4) & 7 else '')
            elif mode == 1: d = ('JVB' if ins & 0x40 else 'JMP') + (' $%04X' % (rb(a + 1) | rb(a + 2) << 8) if n == 3 else '')
            else:
                d = 'mode %X' % mode
                if ins & 0x40 and n == 3: d += ' LMS $%04X' % (rb(a + 1) | rb(a + 2) << 8)
                if ins & 0x10: d += ' +HSCROL'
                if ins & 0x20: d += ' +VSCROL'
            if ins & 0x80: d += ' +DLI'
            cm0 = comments.get(a, '')
            emit(lbl, '.byte ' + ','.join('$%02X' % rb(x) for x in range(a, stop)), (cm0 + '  ' if cm0 else '') + d)
            a = stop
            continue
        bs = [rb(x) for x in range(a, stop)]
        cm = comments.get(a, '')
        if kind == 'word' and len(bs) % 2 == 0:
            body = '.word ' + ','.join(sym_abs(bs[i] | bs[i + 1] << 8, None) for i in range(0, len(bs), 2))
        else:
            body = '.byte ' + ','.join('$%02X' % b for b in bs)
            if kind == 'text':
                t = ''.join(scr(b) for b in bs)
                cm = (cm + '  ' if cm else '') + '"%s"' % t
            elif kind == 'gfx':
                cm = (cm + '  ' if cm else '') + ' '.join(format(b, '08b').replace('0', '.').replace('1', '#') for b in bs)
            elif kind == 'gfx2':
                cm = (cm + '  ' if cm else '') + ' '.join(''.join('.123'[(b >> sh) & 3] for sh in (6, 4, 2, 0)) for b in bs)
        emit(lbl, body, cm)
        a = stop
    if cur_reloc and a > cur_reloc[1]:
        out.append('        .org $%04X                      ; --- back to cartridge addresses ---' % a)
        out.append('')
        cur_reloc = None

open(sys.argv[1] if len(sys.argv) > 1 else 'miner2049er.asm', 'w').write('\n'.join(out) + '\n')
print('lines', len(out), 'code instrs', len(code), 'bad', ['%04X' % b for b in bad])
