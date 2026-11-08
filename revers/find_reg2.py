import struct
DLL = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
data=open(DLL,'rb').read()
val=0xEBF22B0
for width,fmt in ((4,'<I'),(8,'<Q')):
    n=struct.pack(fmt,val)
    hits=[];i=0
    while True:
        i=data.find(n,i)
        if i==-1:break
        hits.append(i);i+=1
    print(width,"hits",len(hits),[hex(h) for h in hits[:10]])
# flat-array hypothesis: base = arr - first_field*4
ff=59180
base=0xEBF22B0-ff*4
print("flat base",hex(base))
print("in rdata?", 0xebb2e00 <= base < 0xebb2e00+0x20c6800)
for i in range(10):
    p=base+i*4
    print(i, hex(struct.unpack_from('<I',data,p)[0]))
print("check arr-3 index at flat:",hex(struct.unpack_from('<i',data,base+(ff+3)*4)[0]))
