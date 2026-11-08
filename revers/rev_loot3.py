import pefile, capstone, struct, bisect
PATH=r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
pe=pefile.PE(PATH,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
DATA=open(PATH,"rb").read()
def va2off(va): return pe.get_offset_from_rva(va)
pd=[s for s in pe.sections if s.Name.rstrip(b'\0')==b'.pdata'][0]
blob=DATA[pd.PointerToRawData:pd.PointerToRawData+pd.Misc_VirtualSize]
funcs=[]
for i in range(0,len(blob)-12,12):
    b,e,u=struct.unpack_from("<III",blob,i)
    if e>b: funcs.append((b,e))
funcs.sort(); starts=[b for b,e in funcs]
def func_of(va):
    i=bisect.bisect_right(starts,va)-1
    if i<0: return None
    b,e=funcs[i]
    return (b,e) if b<=va<e else None
def dis(va,label=None):
    f=func_of(va)
    if not f: print("\n### 0x%X NO PDATA"%va); return
    b,e=f
    label=label or ""
    o=va2off(b); code=DATA[o:o+(e-b)]
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64); md.detail=True
    print("\n===== %s RVA 0x%X..0x%X ======"%(label,b,e))
    for ins in md.disasm(code,IB+b):
        note=""
        for op in ins.operands:
            if op.type==capstone.x86.X86_OP_MEM and op.mem.base==capstone.x86.X86_REG_RIP:
                note=" ; ->0x%X"%(ins.address+ins.size+op.mem.disp-IB)
        print("0x%X  %-18s %s %s%s"%(ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str,note))
    print("===== end =====")

for va,lab in [(0x35AFAC0,"a4f525 (uses +28/+30/+38)"),
               (0x35B1080,"fae5b9"),
               (0x35B33A0,"9054fa"),
               (0x35B0860,"tiny getter +30"),
               (0x35B0C30,"tiny getter2"),
               (0x35B6160,"target of a4f525"),
               (0x35B4240,"target of 9054fa")]:
    dis(va,lab)
