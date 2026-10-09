#!/usr/bin/env python3
"""Build the Miner 2049er HTML book from src/*.md + template + data."""
import os as _os, sys as _sys
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '../..'))
for _d in ('tools', 'emulator', 'web/tools'):
    if _os.path.join(REPO, _d) not in _sys.path: _sys.path.insert(0, _os.path.join(REPO, _d))

import re, json, html, glob, os, base64, sys
ROOT = _os.path.join(REPO, 'web')
SRC = sorted(glob.glob(_os.path.join(REPO, 'book', 'chapters', '0*.md')))
OUT = ROOT + '/out'
ASM = _os.path.join(REPO, 'src/miner2049er.asm')

# ---------------------------------------------------------------- labels for auto-linking
labels = set()
for line in open(ASM):
    m = re.match(r'^([A-Z][A-Z0-9_]{2,}):', line)
    if m: labels.add(m.group(1))
    m = re.match(r'^([A-Z][A-Z0-9_]{2,})\s+=', line)
    if m: labels.add(m.group(1))
# words that are labels but read as ordinary words / register names in prose
NOLINK = {'STATION', 'ZONE', 'SCORE', 'DLIST', 'STATUS', 'BITMAP', 'ITEMS', 'PORTA', 'PACTL', 'CONSOL', 'DMACTL', 'CHACTL',
          'HSCROL', 'PMBASE', 'CHBASE', 'WSYNC', 'VCOUNT', 'NMIEN', 'NMIRES', 'DLISTL', 'DLISTH', 'TEXT_RAM', 'SPECIAL', 'ALIVE',
          'PLAYER', 'PTR', 'KILLED', 'DYING', 'FRAMES', 'PAUSED'}

def esc(s): return html.escape(s, quote=False)

def inline(s):
    # code spans first (protect)
    parts = re.split(r'(`[^`]+`)', s)
    out = []
    for p in parts:
        if p.startswith('`') and p.endswith('`') and len(p) > 1:
            out.append('<code>' + esc(p[1:-1]) + '</code>')
            continue
        t = esc(p)
        t = re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+(?:\([^)]*\))?[^)\s]*)\)', lambda m: '<a href="%s" target="_blank" rel="noopener">%s</a>' % (m.group(2), m.group(1)), t)
        t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
        t = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<em>\1</em>', t)
        def lk(m):
            w = m.group(0)
            if w in labels and w not in NOLINK and ('_' in w or len(w) >= 6):
                return '<a class="sym" href="#L-%s" data-sym="%s">%s</a>' % (w, w, w)
            return w
        # avoid linking inside tags: split on tags
        segs = re.split(r'(<[^>]+>)', t)
        inside_a = False
        for i, sg in enumerate(segs):
            if sg.startswith('<'):
                if sg.startswith('<a '): inside_a = True
                if sg.startswith('</a'): inside_a = False
                continue
            if not inside_a:
                segs[i] = re.sub(r'\b[A-Z][A-Z0-9_]{2,}\b', lk, sg)
        out.append(''.join(segs))
    return ''.join(out)

def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')

ASM_KW = re.compile(r'^(\s*)([A-Za-z_][A-Za-z0-9_]*:)?(\s*)([a-zA-Z]{3})?(\b.*?)(;.*)?$')
def hl_asm(code):
    out = []
    for line in code.split('\n'):
        m = re.match(r'^(\$[0-9A-F]{4}\s+(?:[0-9A-F]{2}\s)*\s*)(.*)$', line)
        pre = ''
        if m and re.match(r'^\$[0-9A-F]{4}\s', line):
            pre = '<span class="ad">' + esc(m.group(1)) + '</span>'; line = m.group(2)
        cm = ''
        if ';' in line:
            i = line.index(';'); cm = '<span class="cm">' + esc(line[i:]) + '</span>'; line = line[:i]
        lab = ''
        m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*:)(.*)$', line)
        if m: lab = '<span class="lb">' + esc(m.group(1)) + '</span>'; line = m.group(2)
        m = re.match(r'^(\s*)(\.?[a-zA-Z]{2,5})(\b.*)$', line)
        if m:
            body = esc(m.group(3))
            body = re.sub(r'(#?\$[0-9A-Fa-f]+|#\d+|\b\d+\b)', r'<span class="nm">\1</span>', body)
            line = esc(m.group(1)) + '<span class="mn">' + esc(m.group(2)) + '</span>' + body
        else:
            line = esc(line)
        out.append(pre + lab + line + cm)
    return '\n'.join(out)

ops = []          # (id, title)
figs = []
toc = []          # (level, id, title)
fignum = [0]

def parse(text):
    lines = text.split('\n')
    out = []; i = 0
    para = []
    def flush():
        if para:
            out.append('<p>' + inline(' '.join(para)) + '</p>'); para.clear()
    while i < len(lines):
        L = lines[i]
        if L.startswith('```'):
            flush(); j = i + 1; buf = []
            while not lines[j].startswith('```'): buf.append(lines[j]); j += 1
            out.append('<pre class="code"><code>' + hl_asm('\n'.join(buf)) + '</code></pre>'); i = j + 1; continue
        m = re.match(r'^(#{1,2}) (.+?)(?: \{#([\w-]+)\})?\s*$', L)
        if m:
            flush(); lvl = len(m.group(1)); t = m.group(2); hid = m.group(3) or slug(t)
            toc.append((lvl, hid, t))
            if lvl == 1:
                out.append('</section><section class="chapter" id="%s"><h1>%s</h1>' % (hid, inline(t)))
            else:
                out.append('<h2 id="%s">%s</h2>' % (hid, inline(t)))
            i += 1; continue
        if L.startswith('!fig '):
            flush(); fid, cap = L[5:].split('|', 1); fignum[0] += 1
            figs.append(fid)
            out.append('<figure class="fig" id="fig-%s" data-fig="%s"><div class="figbody"></div><figcaption><span class="fnum">Figure %d</span> %s</figcaption></figure>' % (fid, fid, fignum[0], inline(cap)))
            i += 1; continue
        if L.strip() == '!opindex':
            flush(); out.append('<!--OPINDEX-->'); i += 1; continue
        if L.startswith(':::op '):
            flush(); title = L[6:].strip(); j = i + 1; fields = {}; body = []
            while not lines[j].startswith(':::'):
                mm = re.match(r'^(name|enc|cycles|flags|body): ?(.*)$', lines[j])
                if mm and mm.group(1) != 'body': fields[mm.group(1)] = mm.group(2)
                elif mm: body.append(mm.group(2))
                else: body.append(lines[j])
                j += 1
            oid = 'op-' + slug(title)
            n = 2
            while any(o[0] == oid for o in ops): oid = 'op-' + slug(title) + '-' + str(n); n += 1
            ops.append((oid, title, fields.get('name', '')))
            chips = ''
            for k, lab in (('enc', 'bytes'), ('cycles', 'cycles'), ('flags', 'flags')):
                if k in fields: chips += '<div class="chip"><span>%s</span><b>%s</b></div>' % (lab, esc(fields[k]))
            kind = 'Z80' if title.startswith('LDIR') else '6502'
            out.append('<aside class="op" id="%s"><div class="ophead"><div class="opkind">%s</div><div class="opmn">%s</div><div class="opname">%s</div></div><div class="opchips">%s</div><div class="opbody"><p>%s</p></div></aside>'
                       % (oid, kind, esc(title), esc(fields.get('name', '')), chips, inline(' '.join(body))))
            i = j + 1; continue
        if L.startswith('|'):
            flush(); rows = []
            while i < len(lines) and lines[i].startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')]); i += 1
            h = '<div class="tbl"><table><thead><tr>' + ''.join('<th>%s</th>' % inline(c) for c in rows[0]) + '</tr></thead><tbody>'
            for r in rows[1:]: h += '<tr>' + ''.join('<td>%s</td>' % inline(c) for c in r) + '</tr>'
            out.append(h + '</tbody></table></div>'); continue
        if re.match(r'^- ', L):
            flush(); items = []
            while i < len(lines) and lines[i].startswith('- '): items.append(lines[i][2:]); i += 1
            out.append('<ul>' + ''.join('<li>%s</li>' % inline(x) for x in items) + '</ul>'); continue
        if re.match(r'^\d+\. ', L):
            flush(); items = []
            while i < len(lines) and re.match(r'^\d+\. ', lines[i]): items.append(re.sub(r'^\d+\. ', '', lines[i])); i += 1
            out.append('<ol>' + ''.join('<li>%s</li>' % inline(x) for x in items) + '</ol>'); continue
        if not L.strip():
            flush(); i += 1; continue
        para.append(L.strip()); i += 1
    flush()
    return '\n'.join(out)

body = ''
for f in SRC:
    body += parse(open(f).read()) + '\n'
body = body.replace('</section>', '', 1) + '</section>'
# op index
oi = '<div class="opindex">' + ''.join('<a href="#%s"><b>%s</b><span>%s</span></a>' % (o[0], esc(o[1]), esc(o[2])) for o in ops) + '</div>'
body = body.replace('<!--OPINDEX-->', '<p>Every opcode note in the book, in the order they appear.</p>' + oi)

# TOC
tl = '<ol class="toc1">'
open1 = False
for lvl, hid, t in toc:
    if lvl == 1:
        if open1: tl += '</ol></li>'
        tl += '<li><a href="#%s">%s</a><ol class="toc2">' % (hid, esc(t)); open1 = True
    else:
        tl += '<li><a href="#%s">%s</a></li>' % (hid, esc(t))
tl += '</ol></li><li><a href="#listing">The listing</a><ol class="toc2"></ol></li></ol>'

# ---------------------------------------------------------------- assets
def b64file(p): return base64.b64encode(open(p, 'rb').read()).decode()
shots = {}
for name in ['st_%d' % n for n in range(1, 11)] + ['prep', 'go_06', 'go_name', 'credits_end']:
    p = _os.path.join(REPO, 'shots/%s.png') % name
    if os.path.exists(p): shots[name] = 'data:image/png;base64,' + b64file(p)
core = json.load(open(OUT + '/data/core.json'))
core['shots'] = shots
movies = {}
for mf in glob.glob(OUT + '/data/*.json'):
    if os.path.basename(mf).startswith('movie_'):
        nm = os.path.basename(mf)[6:-5]; mm = json.load(open(mf))
        mm['bin'] = base64.b64encode(open(OUT + '/data/movie_%s.bin' % nm, 'rb').read()).decode(); movies[nm] = mm
core['movies'] = movies
core['labels'] = sorted(labels)

tpl = open(ROOT + '/tools/template.html').read()
css = open(ROOT + '/tools/style.css').read()
js = open(ROOT + '/tools/app.js').read()
page = tpl.replace('/*CSS*/', css).replace('<!--TOC-->', tl).replace('<!--BODY-->', body)
page = page.replace('/*DATA*/', 'window.M49=' + json.dumps(core, separators=(',', ':')) + ';').replace('/*JS*/', js)
open(OUT + '/index.html', 'w').write(page)
os.system('cp %s %s/data/miner2049er.txt' % (ASM, OUT))
print('figs', len(figs), figs)
print('ops', len(ops), 'toc', len(toc), 'size', len(page))
