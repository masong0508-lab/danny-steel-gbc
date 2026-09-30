import struct
def vlq(d,i):
    v=0
    while True:
        b=d[i]; i+=1; v=(v<<7)|(b&127)
        if not b&128: return v,i
def parse(path):
    d=open(path,'rb').read()
    assert d[:4]==b'MThd'
    fmt,ntr,div=struct.unpack('>HHH',d[8:14]); i=14
    tracks=[]
    for _ in range(ntr):
        assert d[i:i+4]==b'MTrk'; ln=struct.unpack('>I',d[i+4:i+8])[0]; i+=8
        end=i+ln; t=0; run=None; ev=[]
        while i<end:
            dt,i=vlq(d,i); t+=dt; b=d[i]
            if b==0xFF:
                ty=d[i+1]; l,j=vlq(d,i+2); ev.append((t,'meta',ty,bytes(d[j:j+l]))); i=j+l
            elif b in(0xF0,0xF7):
                l,j=vlq(d,i+1); i=j+l
            else:
                if b&128: run=b; i+=1
                st=run; k=st>>4
                n=1 if k in(0xC,0xD) else 2
                ev.append((t,'ch',st,tuple(d[i:i+n]))); i+=n
        tracks.append(ev)
    return fmt,div,tracks
if __name__=='__main__':
    import sys
    fmt,div,tr=parse(sys.argv[1]); print('fmt',fmt,'div',div,'tracks',len(tr))
    for n,ev in enumerate(tr):
        names=[e for e in ev if e[1]=='meta' and e[2] in(3,4)]
        prog=[(e[2]&15,e[3][0]) for e in ev if e[1]=='ch' and e[2]>>4==0xC]
        notes=[e for e in ev if e[1]=='ch' and e[2]>>4==9 and e[3][1]>0]
        chs=sorted(set(e[2]&15 for e in notes))
        print(n,'events',len(ev),'notes',len(notes),'ch',chs,'prog',prog,[x[3] for x in names])
        for e in ev:
            if e[1]=='meta' and e[2] in(0x51,0x58,0x59): print('  meta',hex(e[2]),e[3].hex(),'t',e[0])
        if notes:
            ps=[e[3][0] for e in notes]; print('  pitch',min(ps),max(ps),'last t',max(e[0] for e in ev))
