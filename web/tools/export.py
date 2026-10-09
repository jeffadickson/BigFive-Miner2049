import os as _os, sys as _sys
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '../..'))
for _d in ('tools', 'emulator', 'web/tools'):
    if _os.path.join(REPO, _d) not in _sys.path: _sys.path.insert(0, _os.path.join(REPO, _d))

import json, base64, sys
from render import atari_rgb
ROM=open(_os.path.join(REPO, 'rom/miner.rom'),'rb').read()
st=json.load(open(_os.path.join(REPO, 'tools/analysis/stations.json')))
kt=json.load(open(_os.path.join(REPO, 'tools/analysis/kernel_trace.json')))
pal=['%02x%02x%02x'%atari_rgb(c) for c in range(256)]
d={'rom':base64.b64encode(ROM).decode(),
   'pal':pal,
   'st1':{'bitmap':st['1']['bitmap'],'c':[st['1']['colbk'],st['1']['c1'],st['1']['c2'],st['1']['c3']],'pm':st['1']['pm'],'mut':st['1']['mut'],'bob':st['1']['bob']},
   'ktrace':{k:v for k,v in kt.items()}}
open(_os.path.join(REPO, 'web/out/data/core.json'),'w').write(json.dumps(d,separators=(',',':')))
print(len(json.dumps(d)))
