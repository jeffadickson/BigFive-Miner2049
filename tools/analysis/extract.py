import os as _os, sys as _sys
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '../..'))
for _d in ('tools', 'emulator', 'web/tools'):
    if _os.path.join(REPO, _d) not in _sys.path: _sys.path.insert(0, _os.path.join(REPO, _d))

import sys, json, base64
from station import build
out={}
for n in range(1,11):
    at=build(n,250)
    r=at.ram
    out[n]={'bitmap':base64.b64encode(bytes(r[0x2100:0x3DC0])).decode(),
            'colbk':r[0x8A],'c1':r[0x8B],'c2':r[0x8C],'c3':r[0x8D],
            'sections':r[0xF6],'bob':[r[0x90],r[0x91]],
            'pm':base64.b64encode(bytes(r[0x0300:0x0800])).decode(),
            'mut':list(r[0x09C0:0x09C0+88]),'items':list(r[0x0992:0x09C0])}
    print(n, r[0xF6], hex(r[0x8B]),hex(r[0x8C]),hex(r[0x8D]), r[0x90], r[0x91])
json.dump(out,open('stations.json','w'))
