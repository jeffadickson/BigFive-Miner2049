import os as _os, sys as _sys
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '../..'))
for _d in ('tools', 'emulator', 'web/tools'):
    if _os.path.join(REPO, _d) not in _sys.path: _sys.path.insert(0, _os.path.join(REPO, _d))

import zipfile, re, sys, shutil
src = sys.argv[1]
zin = zipfile.ZipFile(src)
items = {n: zin.read(n) for n in zin.namelist()}
zin.close()
doc = items['word/document.xml'].decode('utf8')
counter = [0]; stack = []
def fix(m):
    tag = m.group(0)
    if tag.startswith('<w:bookmarkStart'):
        counter[0] += 1; stack.append(counter[0])
        return re.sub(r'w:id="[^"]*"', 'w:id="%d"' % counter[0], tag)
    return re.sub(r'w:id="[^"]*"', 'w:id="%d"' % stack.pop(0), tag)
doc = re.sub(r'<w:bookmark(?:Start|End)\b[^>]*/>', fix, doc)
items['word/document.xml'] = doc.encode('utf8')
with zipfile.ZipFile(src + '.tmp', 'w', zipfile.ZIP_DEFLATED) as z:
    for n, b in items.items(): z.writestr(n, b)
shutil.move(src + '.tmp', src)
print('bookmarks', counter[0])
