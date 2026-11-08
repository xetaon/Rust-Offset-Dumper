import pefile, capstone, struct, bisect
PATH=r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
pe=pefile.PE(PATH,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
DATA=open(PATH,"rb").read()
def va2off(va): return pe.get_offset_from_rva(va)
def dis(va,size,label):
    o=va2off(va); code=DATA[o:o+size]
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64); md.detail=True
    print("\n===== %s RVA 0x%X size 0x%X ====="%(label,va,size))
    for ins in md.disasm(code,IB+va):
        # annotate rip-relative
        note=""
        for op in ins.operands:
            if op.type==capstone.x86.X86_OP_MEM and op.mem.base==capstone.x86.X86_REG_RIP:
                tgt=ins.address+ins.size+op.mem.disp
                note=" ; ->0x%X"%(tgt-IB)
        print("0x%X  %-20s %s %s%s"%(ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str,note))
    print("===== end =====")

# pdata
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
("%ffb241e1420decb1981ec44c77eada17c1499d46",0x7FF9F631EBD0),
("%072bb5c037300079615d7f29845c83721c1e6efe",0x7FF9F631EDD0),
("%caecbb99e8a039a15c10895b74bf3a22ecacc045",0x7FF9F631F150),
("%e9848751b42bd5d9d094cfb66339ffcf14b48750",0x7FF9F365A3D0),
("%b49c399947a906cbc117702ac8b53ddfb089590e",0x7FF9F631F2C0),
("%df4c34a56f9de13342f15e0c12d5bc3e7423130a",0x7FF9F631F2D0),
("%b7f30a8b30ac51e3756c7459665ed2c0bf3268ac",0x7FF9F631F440),
("%0158c8e7d99531624beb46f11d189e07c3d2359a",0x7FF9F631F8C0),
("%78c62d1f21f9b99ee58c3533249b4b9faf388f08",0x7FF9F631F910),
("%fbdc9190d1c247ddc2e46c17f4f93b62b446ae1f",0x7FF9F631F920),
("%a4f525aab4ae466152fc6ca723e488ef21f7eb9a",0x7FF9F631FAC0),
("%f6fa0e5a7796b34d2620616eb1b07a0ac889c9dd",0x7FF9F631FBD0),
("%17466725a27711ea33c1c6cbe01e9fe01e079ac6",0x7FF9F6320150),
("%28b11b0bd364b9c5adfa2643f3a4b276eae4ee93",0x7FF9F63206D0),
("%89bfe02443d205014ed68c2d7838f240796c2a91",0x7FF9F6320860),
("%d36623696f4b46096f264b27593b823e95e59cbb",0x7FF9F63208B0),
("%f7b76614bae4879aecc65ae7f46446dcb6ae983b",0x7FF9F6320C30),
("%2636ebcdf7a8b5243ef74dee71bcced63765f4be",0x7FF9F6320C90),
("%3d435ae6a62b2888c3d867daaf54fecff9506fc9",0x7FF9F6320CF0),
("%24648b7830a5fa93686f153d72bb5d2b3bcf2b1b",0x7FF9F6320EF0),
("%fae5b98e02a03167ab4e754f47cc8c0ea119e243",0x7FF9F6321080),
("%c8ca33d18804c0538e36bd2b2681a536f0f0bddc",0x7FF9F6321190),
("%7271beed61522db866511eb0baaf421361487582",0x7FF9F63211F0),
("%4a98194c66d6bd83d36a87c491f7c08f9b8dd2ab",0x7FF9F6321360),
("%d12f8d13e3ca343e023c1d15bda23a9e58be48b7",0x7FF9F63218E0),
("%e1202db57ddb131526d822705577e946d3b4d7fb",0x7FF9F6321AE0),
("%f522d81eb170fbaccc31233a2e50039ddeb369a9",0x7FF9F365A3D0),
("%dac4f03464d58357c06534135fe36ba7dc78e5d0",0x7FF9F6321C70),
(".ctor",0x7FF9F6321FF0),
("%1bcf10ad2688ebd095d3a1d0d98f73a92e9c2eab",0x7FF9F6322100),
("%7acc5854199092207cf96ac0d0abacc755431295",0x7FF9F63222A0),
("%55694f248c65d4565747d5313c5ee563e608d44b",0x7FF9F6322710),
("%14c0ba50874d3c09be6e1e1b1ea76dc26b0204bb",0x7FF9F63228A0),
("%30c057b9a82da0d988fd19b7fc1d2afd658e1a5b",0x7FF9F6322A30),
("%39872d11293280c51f1df0790935f19e94b6faea",0x7FF9F6322FB0),
("%9ee19bbaf87475cba56e67864c5e1070d157651d",0x7FF9F6322FC0),
("%0158c8e7d99531624beb46f11d189e07c3d2359a#2",0x7FF9F6323340),
("%9054fa2f541e63f050d3e62ad774f7da5970f1be",0x7FF9F63233A0),
("%4c3b9401f0dc6f916d0c12fcdbd0e900fb6ea57e",0x7FF9F63234B0),
]
print("OnClicked func:", func_of(0x463DB40) and tuple(hex(x) for x in func_of(0x463DB40)))
b,e=func_of(0x463DB40)
dis(b,e-b,"LootAllButton.OnClicked")

print("\n\n##### PlayerLoot methods: size + calls #####")
for name,ptr in pairs:
    rva=ptr-base
    f=func_of(rva)
    if not f:
        print("%-46s ptr=0x%X rva=0x%X  NO PDATA"%(name,ptr,rva)); continue
    b,e=f
    o=va2off(b); code=DATA[o:o+(e-b)]
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
    calls=[]
    for ins in md.disasm(code,IB+b):
        if ins.mnemonic=="call":
            try:
                t=ins.operands[0]
                if t.type==capstone.x86.X86_OP_IMM:
                    calls.append(ins.address+ins.size and (t.imm-IB))
            except Exception: pass
    print("%-46s rva=0x%-8X size=0x%-5X calls=%s"%(name,rva,e-b,[hex(c) for c in calls[:8]]))
