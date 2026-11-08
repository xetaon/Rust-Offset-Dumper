import struct
P=r"C:\Program Files (x86)\Steam\steamapps\common\Rust\RustClient_Data\il2cpp_data\Metadata\global-metadata.dat"
b=open(P,'rb').read()
ints=[]
for i in range(0,0x17C,4):
    ints.append(struct.unpack_from("<i",b,i)[0])
# candidate (offset,size) pairs are consecutive ints; both positive
best=[]
HEAP=0x29F25D8; HSZ=0x1947CA
HEND=HEAP+HSZ
print("heap range 0x%X..0x%X size=0x%X"%(HEAP,HEND,HSZ))
for i in range(2,len(ints)-1):
    off,size=ints[i],ints[i+1]
    if off<0x1000 or size<=0 or off+size>len(b): continue
    for stride in range(0x40,0x90):
        cnt=(size//stride)
        if cnt<50 or cnt>200000: continue
        good=0; n=0
        for k in range(0,min(cnt,400)):
            v=struct.unpack_from("<i",b,off+k*stride)[0]
            n+=1
            if HEAP<=v<HEND: good+=1
        frac=good/max(n,1)
        if frac>0.5:
            best.append((frac,i,off,size,stride,cnt))
best.sort(reverse=True)
print("candidates where first-int32 points into heap:")
for x in best[:30]:
    print("  frac=%.2f idx=%d off=0x%X size=0x%X stride=0x%X count=%d"%x)
