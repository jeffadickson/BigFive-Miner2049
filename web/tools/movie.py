"""Encode a sequence of PNG frames as a sparse XOR-delta movie.
Format (after zlib): for each frame: u32 nbytes, then runs: varint skip, varint count, count bytes (XOR with previous frame);
frame 0 is XOR against an all-zero frame.  Palette indices, w*h bytes per frame."""
import os as _os, sys as _sys
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '../..'))
for _d in ('tools', 'emulator', 'web/tools'):
    if _os.path.join(REPO, _d) not in _sys.path: _sys.path.insert(0, _os.path.join(REPO, _d))

import sys, zlib, json, struct
from PIL import Image
import numpy as np
def varint(n):
    out=bytearray()
    while True:
        b=n&0x7F; n>>=7
        if n: out.append(b|0x80)
        else: out.append(b); return out
def encode(files, out, fps=30, crop=None, meta=None):
    pal={}; frames=[]
    for f in files:
        im=Image.open(f).convert('RGB')
        if crop: im=im.crop(crop)
        a=np.array(im).reshape(-1,3)
        key=(a[:,0].astype(np.uint32)<<16)|(a[:,1].astype(np.uint32)<<8)|a[:,2]
        frames.append(key)
    allk=np.unique(np.concatenate([np.unique(k) for k in frames]))
    assert len(allk)<=256, len(allk)
    lut={int(k):i for i,k in enumerate(allk)}
    w,h=im.size
    prev=np.zeros(w*h,np.uint8); buf=bytearray()
    for key in frames:
        idx=np.searchsorted(allk,key).astype(np.uint8)
        x=idx^prev; prev=idx
        nz=np.flatnonzero(x)
        fb=bytearray(); pos=0
        if len(nz):
            # group into runs allowing small zero gaps (<4)
            starts=[nz[0]]; ends=[]
            for a,b in zip(nz[:-1],nz[1:]):
                if b-a>4: ends.append(a+1); starts.append(b)
            ends.append(nz[-1]+1)
            for s,e in zip(starts,ends):
                fb+=varint(int(s-pos)); fb+=varint(int(e-s)); fb+=bytes(x[s:e]); pos=e
        buf+=struct.pack('<I',len(fb))+fb
    z=zlib.compress(bytes(buf),9)
    open(out,'wb').write(z)
    info={'w':w,'h':h,'n':len(frames),'fps':fps,'pal':['%06x'%int(k) for k in allk]}
    if meta: info.update(meta)
    return info,len(z)
if __name__=='__main__':
    import glob
    files=sorted(glob.glob(sys.argv[1]+'/*.png'))[int(sys.argv[3]):int(sys.argv[4])]
    info,n=encode(files,sys.argv[2])
    print(info['n'],len(info['pal']),n)
