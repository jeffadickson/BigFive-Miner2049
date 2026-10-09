import os as _os, sys as _sys
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '../..'))
for _d in ('tools', 'emulator', 'web/tools'):
    if _os.path.join(REPO, _d) not in _sys.path: _sys.path.insert(0, _os.path.join(REPO, _d))

import sys
from station import build
at=build(1,300)
c=at.cpu
res={'dli':[], 'vbi':[]}
state={'start':None,'kind':None,'depth':0}
def hook(a,pc):
    if pc==0xB70E: state['start']=c.processorCycles; state['kind']='dli'
    if pc==0xBBB0: state['start']=c.processorCycles; state['kind']='vbi'
    if pc==0x923C and state['start'] is not None:
        # NMI_EXIT: count to RTI ~ few cycles
        res[state['kind']].append(c.processorCycles-state['start']); state['start']=None
for f in range(60): at.run_frame(hook)
import statistics
for k,v in res.items():
    print(k, len(v), min(v), max(v), statistics.mean(v))
