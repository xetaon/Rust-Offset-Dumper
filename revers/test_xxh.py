import struct, os
P1=2654435761; P2=2246822519; P3=3266489917; P4=668265263; P5=374761393
def rotl(x,n): return ((x<<n)|(x>>(32-n)))&0xffffffff
def rnd(acc,x): return (rotl((acc + x*P2)&0xffffffff,13)*P1)&0xffffffff
def xxh32(data,seed=0):
    n=len(data); p=0; h=0
    if n>=16:
        v1=(seed+P1+P2)&0xffffffff; v2=(seed+P2)&0xffffffff; v3=seed&0xffffffff; v4=(seed-P1)&0xffffffff
        while p+16<=n:
            v1=rnd(v1,struct.unpack_from('<I',data,p)[0]); v2=rnd(v2,struct.unpack_from('<I',data,p+4)[0]); v3=rnd(v3,struct.unpack_from('<I',data,p+8)[0]); v4=rnd(v4,struct.unpack_from('<I',data,p+12)[0]); p+=16
        h=(rotl(v1,1)+rotl(v2,7)+rotl(v3,12)+rotl(v4,18))&0xffffffff
    else:
        h=(seed+P5)&0xffffffff
    h=(h+n)&0xffffffff
    while p+4<=n:
        h=(rotl((h+struct.unpack_from('<I',data,p)[0]*P3)&0xffffffff,17)*P4)&0xffffffff; p+=4
    while p<n:
        h=(rotl((h+data[p]*P5)&0xffffffff,11)*P1)&0xffffffff; p+=1
    h^=h>>15; h=(h*P2)&0xffffffff; h^=h>>13; h=(h*P3)&0xffffffff; h^=h>>16
    return h
for s,e in [(b'',0),(b'a',0),(b'abc',0),(b'message digest',0),(b'abcdefghijklmnopqrstuvwxyz',0)]:
    print(s, hex(xxh32(s,e)))
for n in [0,1,4,16,17,64,1000]:
    data=os.urandom(n)
    h=xxh32(data,42)
    key=struct.pack('<I',h)
    enc=bytes(b ^ ((key[i%4]+i*41)&0xff) for i,b in enumerate(data))
    h2=xxh32(enc,42)
    print('n',n,'orig',hex(h),'enc',hex(h2),'invariant',h==h2)
