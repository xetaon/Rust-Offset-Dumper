import struct
DLL=r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
data=open(DLL,'rb').read()
def find(vals,name):
    pat=b"".join(struct.pack("<I",v) for v in vals)
    hits=[];i=0
    while True:
        i=data.find(pat,i)
        if i==-1:break
        hits.append(i);i+=1
    print(name,len(hits),[hex(h) for h in hits[:10]])
find([0x140,0x164,0x170,0x17c,0x180],"Proj-live-seq")
find([0x164,0x170,0x17c,0x180,0x188,0x194],"Proj-live-seq2")
find([0x140,0x144,0x148,0x14c],"Proj-live-near")
# full projectile array 74
b=0xec2cb08
print("proj full:", [hex(x) for x in struct.unpack_from('<74i',data,b)])
# check metadata sentinel meaning: count arrays ending patterns
