import os as _os, sys as _sys
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '../..'))
for _d in ('tools', 'emulator', 'web/tools'):
    if _os.path.join(REPO, _d) not in _sys.path: _sys.path.insert(0, _os.path.join(REPO, _d))

import json, subprocess, re
toc = json.load(open('toc.json'))
n = int(re.search(r'Pages:\s+(\d+)', subprocess.run(['pdfinfo', 'render/mc.pdf'], capture_output=True, text=True).stdout).group(1))
texts = []
for p in range(1, n + 1):
    t = subprocess.run(['pdftotext', '-f', str(p), '-l', str(p), '-layout', 'render/mc.pdf', '-'], capture_output=True, text=True).stdout
    texts.append([l.strip() for l in t.split('\n')])
pages = {}
start = next(p for p in range(1, n + 1) if any('came out for the Atari 400' in l for l in texts[p - 1]))
for e in toc:
    for p in range(start, n + 1):
        if e['text'] in texts[p - 1]:
            # printed page number = physical page - 1 (title page has no number but counts? footer starts in section 2)
            pages[e['text']] = p
            start = p
            break
# the footer page numbers count from the title page (docx continues numbering), so physical = printed
json.dump(pages, open('pages.json', 'w'), indent=0)
missing = [e['text'] for e in toc if e['text'] not in pages]
print(len(pages), 'found; missing', missing)
