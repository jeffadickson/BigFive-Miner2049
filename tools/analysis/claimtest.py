import os as _os, sys as _sys
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '../..'))
for _d in ('tools', 'emulator', 'web/tools'):
    if _os.path.join(REPO, _d) not in _sys.path: _sys.path.insert(0, _os.path.join(REPO, _d))

import sys, json, base64, random
from station import build
ROM=open(_os.path.join(REPO, 'rom/miner.rom'),'rb').read()
def rom(a): return ROM[a-0x8000]
FEET=[rom(0xBFE5+i) for i in range(14)]
# ---- python port (mirrors the JS that will go in the page) ----
def line_addr(r,y):
    if y>=0xC0 or y<8: y=8
    return r[0x3DB8+y] | r[0x3E70+y]<<8
def read_px(r,xpm,y):
    p=(xpm-0x30)&0xFF; b=r[line_addr(r,y)+(p>>2)]
    return (b>>(6-2*(p&3)))&3
def plot(r,x,y,c):
    a=line_addr(r,y)+(x>>2); s=6-2*(x&3)
    r[a]=(r[a]&~(3<<s)&0xFF)|(c<<s)
def claim_at(r,bobx,boby,off):
    x=(bobx+off)&0xFF; y=boby+0x15
    if read_px(r,x,y)!=3: return 0
    y+=1
    if read_px(r,x,y)!=3: n=3
    else:
        y+=1
        if read_px(r,x,y)==3: return 0
        n=2
    x=(x-1)&0xFF
    if read_px(r,x,y)==3: pass
    else:
        cnt=3; edge=False
        while True:
            x=(x-1)&0xFF
            if x==0x2F:
                x=(x+5-cnt)&0xFF; edge=True; break
            if read_px(r,x,y)==3: break
            cnt-=1
            if cnt==0:
                x=(x+5)&0xFF; break
            # loop
        else: pass
        if edge or cnt==0:
            if edge:
                pass
            g=0
            while read_px(r,x,y)!=3 and g<300: x=(x+1)&0xFF; g+=1
            x=(x-5)&0xFF
    x=(x+1)&0xFF; px=(x-0x30)&0xFF
    for row in range(n):
        for k in range(4): plot(r,(px+k)&0xFF,y,3)
        y+=2
    return 1
def claim_floor(r):
    fr=r[0x92]; bx,by=r[0x90],r[0x91]
    a,b=FEET[2*fr],FEET[2*fr+1]
    n=claim_at(r,bx,by,b); n+=claim_at(r,bx,by,a)
    return n
# ---- harness run ----
def call(at,addr):
    c=at.cpu; sent=0xF060
    ret=sent-1; c.stPush(ret>>8); c.stPush(ret&0xFF); c.pc=addr
    n=0
    while c.pc!=sent and n<20000: c.step(); n+=1
    return n
at=build(1,250)
base=bytes(at.ram)
mism=0; tests=0; claims=0
random.seed(1)
st=json.load(open('stations.json'))
for station in (1,2,3,4,5,6,7,8,9,10):
    at=build(station,250); base=bytes(at.ram)
    for t in range(150):
        at.ram[:]=base
        # random position where feet on a girder top line
        fr=random.randrange(0,7)
        while True:
            x=random.randrange(0x31,0xC8); y=random.randrange(9,0xBF)
            if read_px(base,x,y)==3 and read_px(base,x,y-1)!=3: break
        bx=(x-FEET[2*fr+random.randrange(2)])&0xFF; by=y-0x15
        if by==0xAA: continue
        at.ram[0x90]=bx; at.ram[0x91]=by; at.ram[0x92]=fr
        for a in (0xFE,):at.ram[a]=7
        for a in (0xFF,0xB4,0x93,0xAA,0xA3): at.ram[a]=0
        py=bytearray(base); py[0x90]=bx; py[0x91]=by; py[0x92]=fr
        s0=at.ram[0xF6]
        if call(at,0xB625)>=20000: hang=globals().get('hang',0)+1; globals()['hang']=hang; continue
        nclaim=claim_floor(py)
        tests+=1
        ok = bytes(at.ram[0x2100:0x3DC0])==bytes(py[0x2100:0x3DC0]) and (s0-at.ram[0xF6])==nclaim
        claims+=nclaim
        if not ok:
            mism+=1
            if mism<5: print('mismatch',station,hex(bx),by,fr,s0-at.ram[0xF6],nclaim)
    print('station',station,tests,mism,flush=True)
print('tests',tests,'claims',claims,'mismatches',mism,'rom hangs skipped',globals().get('hang',0))
