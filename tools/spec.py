import os as _os, sys as _sys
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
for _d in ('tools', 'emulator', 'web/tools'):
    if _os.path.join(REPO, _d) not in _sys.path: _sys.path.insert(0, _os.path.join(REPO, _d))

import sys,os; from trace import decode, rb
FMT = {'imp': '', 'acc': 'A', 'imm': '#$%02X', 'zp': '$%02X', 'zpx': '$%02X,X', 'zpy': '$%02X,Y','abs': '$%04X', 'absx': '$%04X,X', 'absy': '$%04X,Y', 'ind': '($%04X)', 'indx': '($%02X,X)','indy': '($%02X),Y', 'rel': '$%04X'}
a=int(sys.argv[1],16); e=int(sys.argv[2],16)
while a<=e:
    d=decode(a)
    if not d: print('%04X  ?? %02X'%(a,rb(a))); a+=1; continue
    mn,md,n,v=d; f=FMT[md]
    print('%04X  %-9s %s %s'%(a,' '.join('%02X'%rb(a+i) for i in range(n)),mn,f%v if '%' in f else f)); a+=n
