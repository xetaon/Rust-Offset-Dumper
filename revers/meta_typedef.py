import struct
P=r"C:\Program Files (x86)\Steam\steamapps\common\Rust\RustClient_Data\il2cpp_data\Metadata\global-metadata.dat"
b=open(P,'rb').read()
ints=[struct.unpack_from("<i",b,i)[0] for i in range(0,0x17C,4)]
HEAP_OFF=0x29F25D8; HSZ=0x1947CA
print("candidate string heap 0x%X size 0x%X"%(HEAP_OFF,HSZ))
# verify: heap should contain many NUL bytes and printable ascii
sample=b[HEAP_OFF:HEAP_OFF+0x4000]
print("ascii ratio %.3f  nul ratio %.3f"%(
    sum(1 for c in sample if 32<=c<127)/len(sample),
    sample.count(0)/len(sample)))

results=[]
for i in range(2,len(ints)-1):
    off,size=ints[i],ints[i+1]
    if off<0x1000 or size<=0 or off+size>len(b): continue
    for stride in range(0x40,0x90):
        cnt=size//stride
        if cnt<100: continue
        good=0;n=0
        for k in range(0,min(cnt,300)):
            nameidx,nsidx=struct.unpack_from("<ii",b,off+k*stride)
            n+=1
            if 0<=nameidx<HSZ and 0<=nsidx<HSZ: good+=1
        frac=good/n
        if frac>0.85:
            results.append((frac,i,off,size,stride,cnt))
results.sort(reverse=True)
print("\ntype-def-like tables (both name and namespace in heap):")
for x in results[:20]:
    print("  frac=%.2f idx=%d off=0x%X size=0x%X stride=0x%X count=%d"%x)
