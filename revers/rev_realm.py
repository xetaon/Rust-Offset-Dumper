import pefile, capstone, struct
PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
pe = pefile.PE(PATH, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
DATA = open(PATH,"rb").read()

def va2off(va): return pe.get_offset_from_rva(va)
def dis(va,size,label):
    o=va2off(va); code=DATA[o:o+size]
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64); md.detail=True
    print("\n===== %s 0x%X..0x%X ====="%(label,va,va+size))
    for ins in md.disasm(code,IB+va):
        print("0x%X  %-20s %s %s"%(ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str))
    print("===== end =====")

# parse pdata
pd=[s for s in pe.sections if s.Name.rstrip(b'\0')==b'.pdata'][0]
blob=DATA[pd.PointerToRawData:pd.PointerToRawData+pd.Misc_VirtualSize]
funcs=[]
for i in range(0,len(blob)-12,12):
    beg,end,unw=struct.unpack_from("<III",blob,i)
    if beg==0 and end==0: continue
    if end<=beg: continue
    funcs.append((beg,end))
funcs.sort()
import bisect
starts=[b for b,e in funcs]
def func_of(va):
    i=bisect.bisect_right(starts,va)-1
    if i<0: return None
    b,e=funcs[i]
    if b<=va<e: return (b,e)
    return None

F=func_of(0x1C3A32F)
print("getter func containing 0x1C3A32F:", F and (hex(F[0]),hex(F[1]),hex(F[1]-F[0])))
if F:
    dis(F[0], min(F[1]-F[0], 0x300), "clientEntities getter")

# find callers of F
if F:
    lo,hi=F
    hits=[]
    for s in pe.sections:
        if not (s.Characteristics & 0x20000000): continue
        va=s.VirtualAddress; vsz=s.Misc_VirtualSize; ro=s.PointerToRawData
        sb=DATA[ro:ro+vsz]
        for i in range(len(sb)-5):
            if sb[i]==0xE8:
                rel=struct.unpack_from("<i",sb,i+1)[0]
                tgt=va+i+5+rel
                if tgt==lo:
                    hits.append(va+i)
    print("\ncallers of getter %s: %d"%(hex(lo),len(hits)))
    for c in hits[:12]:
        print("  0x%X"%c)

# inspect function at 0x11633D8 (inlined clientEntities pattern) aligned
F2=func_of(0x11633D8)
print("\nfunc containing 0x11633D8:", F2 and (hex(F2[0]),hex(F2[1]),hex(F2[1]-F2[0])))
if F2:
    dis(F2[0], min(F2[1]-F2[0],0x260), "inlined clientEntities consumer")
