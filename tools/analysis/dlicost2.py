import os as _os, sys as _sys
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '../..'))
for _d in ('tools', 'emulator', 'web/tools'):
    if _os.path.join(REPO, _d) not in _sys.path: _sys.path.insert(0, _os.path.join(REPO, _d))

import sys, statistics
from station import build
res={}
for st in (1,3,5,8,10):
    at=build(st,300); c=at.cpu
    state={'start':None,'band':None}
    def hook(a,pc):
        if pc==0xB70E: state['start']=c.processorCycles; state['band']=a.ram[BAND]
        if pc==0xBBB0: state['start']=c.processorCycles; state['band']='vbi'
        if pc==0x923C and state['start'] is not None:
            res.setdefault((st,state['band']),[]).append(c.processorCycles-state['start']); state['start']=None
    BAND=int(sys.argv[1],16)
    for f in range(120): at.run_frame(hook)
for k in sorted(res, key=str): v=res[k]; print(k, len(v), min(v), max(v), round(statistics.mean(v)))
