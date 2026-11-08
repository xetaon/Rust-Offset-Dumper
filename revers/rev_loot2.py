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
base=0x7FF9F2D70000
pairs=[
("%ffb241",0x7FF9F631EBD0),("%072bb5",0x7FF9F631EDD0),("%caecbb",0x7FF9F631F150),
("%e98487",0x7FF9F365A3D0),("%b49c39",0x7FF9F631F2C0),("%df4c34",0x7FF9F631F2D0),
("%b7f30a",0x7FF9F631F440),("%0158c8#1",0x7FF9F631F8C0),("%78c62d",0x7FF9F631F910),
("%fbdc91",0x7FF9F631F920),("%a4f525",0x7FF9F631FAC0),("%f6fa0e",0x7FF9F631FBD0),
("%174667",0x7FF9F6320150),("%28b11b",0x7FF9F63206D0),("%89bfe0",0x7FF9F6320860),
("%d36623",0x7FF9F63208B0),("%f7b766",0x7FF9F6320C30),("%2636eb",0x7FF9F6320C90),
("%3d435a",0x7FF9F6320CF0),("%24648b",0x7FF9F6320EF0),("%fae5b9",0x7FF9F6321080),
("%c8ca33",0x7FF9F6321190),("%7271be",0x7FF9F63211F0),("%4a9819",0x7FF9F6321360),
("%d12f8d",0x7FF9F63218E0),("%e1202d",0x7FF9F6321AE0),("%f522d8",0x7FF9F365A3D0),
("%dac4f0",0x7FF9F6321C70),(".ctor",0x7FF9F6321FF0),("%1bcf10",0x7FF9F6322100),
("%7acc58",0x7FF9F63222A0),("%55694f",0x7FF9F6322710),("%14c0ba",0x7FF9F63228A0),
("%30c057",0x7FF9F6322A30),("%39872d",0x7FF9F6322FB0),("%9ee19b",0x7FF9F6322FC0),
("%0158c8#2",0x7FF9F6323340),("%9054fa",0x7FF9F63233A0),("%4c3b94",0x7FF9F63234B0),
]
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64); md.detail=True
for name,ptr in pairs:
    rva=ptr-base
    f=func_of(rva)
    if not f:
        print("%-12s rva=0x%-8X NO PDATA (shared/thunk)"%(name,rva)); continue
    b,e=f
    o=va2off(b); code=DATA[o:o+(e-b)]
    calls=[]; offs={}
    for ins in md.disasm(code,IB+b):
        if ins.mnemonic=="call":
            try:
                t=ins.operands[0]
                if t.type==capstone.x86.X86_OP_IMM: calls.append(t.imm-IB)
            except Exception: pass
        for op in ins.operands:
            if op.type==capstone.x86.X86_OP_MEM and op.mem.base and op.mem.disp and op.mem.base not in (capstone.x86.X86_REG_RIP,):
                k="%s+0x%X"%(ins.reg_name(op.mem.base),op.mem.disp & 0xffffffff)
                offs[k]=offs.get(k,0)+1
    top=sorted(offs.items(), key=lambda x:-x[1])[:6]
    print("%-12s rva=0x%-8X size=0x%-5X calls=%s"%(name,rva,e-b,[hex(c) for c in calls[:10]]))
    print("             fields: %s"%(", ".join("%s x%d"%(k,v) for k,v in top)))
