import pefile, capstone, struct, bisect
PATH=r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
pe=pefile.PE(PATH,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
DATA=open(PATH,"rb").read()
def va2off(va): return pe.get_offset_from_rva(va)
# find direct calls to 0x1834DB0
target=0x1834DB0
hits=[]
for s in pe.sections:
    if not (s.Characteristics & 0x20000000): continue
    va=s.VirtualAddress; vsz=s.Misc_VirtualSize; ro=s.PointerToRawData
    sb=DATA[ro:ro+vsz]
    for i in range(len(sb)-5):
        if sb[i]==0xE8:
            rel=struct.unpack_from("<i",sb,i+1)[0]
            if va+i+5+rel==target:
                hits.append(va+i)
print("direct callers of ItemIcon.TryToMove 0x%X: %d"%(target,len(hits)))
for h in hits: print("   0x%X"%h)

# also find pointer occurrences of the function (vtable/methodinfo)
b=struct.pack("<Q",IB+target)
occ=[]; st=0
while True:
    i=DATA.find(b,st)
    if i<0: break
    occ.append(i); st=i+1
print("pointer occurrences: %d"%len(occ))
for i in occ[:20]:
    try: print("   file 0x%X rva 0x%X"%(i, pe.get_rva_from_offset(i)))
    except: pass
