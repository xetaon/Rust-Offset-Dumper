import pefile, capstone, struct
PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
pe = pefile.PE(PATH, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
DATA = open(PATH,"rb").read()

def va2off(va): return pe.get_offset_from_rva(va)
def off2va(o): return pe.get_rva_from_offset(o)+IB

def find_pat(pat, limit=40):
    hits=[]
    for s in pe.sections:
        if not (s.Characteristics & 0x20000000): continue
        va=s.VirtualAddress; vsz=s.Misc_VirtualSize; ro=s.PointerToRawData
        blob=DATA[ro:ro+vsz]
        st=0
        while True:
            i=blob.find(pat,st)
            if i<0: break
            hits.append(va+i); st=i+1
    return hits

def dis(va, count=60, label=""):
    o=va2off(va)
    code=DATA[o:o+count*10]
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64); md.detail=True
    print("\n===== %s @0x%X ====="%(label,va))
    n=0
    for ins in md.disasm(code,IB+va):
        print("0x%X  %-22s %s %s"%(ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str))
        n+=1
        if n>=count: break
    print("===== end =====")

# pattern: mov rax,[rax+0xB8] ; mov rbp,[rax+0x28] ; test rbp,rbp
pat=bytes.fromhex("488B80B8000000488B68284885ED")
hits=find_pat(pat)
print("inlined clientEntities pattern hits: %d"%len(hits))
for h in hits[:20]: print("   0x%X"%h)

# also just mov rax,[rax+0xB8] ; mov rbp,[rax+0x28]
pat2=bytes.fromhex("488B80B8000000488B6828")
h2=find_pat(pat2)
print("\nmov [rax+0xB8];mov [rax+0x28] hits: %d"%len(h2))
for h in h2[:20]: print("   0x%X"%h)

# show one caller of entity_list and context
for c in [0x1070566,0x16523FB]:
    dis(c-120, 110, "caller of entity_list @0x%X"%c)
