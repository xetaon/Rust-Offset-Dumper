import pefile, capstone, struct, bisect, sys
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
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64); md.detail=True
def dis(rva,label,maxn=260):
    f=func_of(rva)
    if not f: print("\n### %s RVA 0x%X NO PDATA"%(label,rva)); return
    b,e=f
    o=va2off(b); code=DATA[o:o+(e-b)]
    print("\n===== %s RVA 0x%X..0x%X size 0x%X ====="%(label,b,e,e-b))
    n=0
    for ins in md.disasm(code,IB+b):
        note=""
        for op in ins.operands:
            if op.type==capstone.x86.X86_OP_MEM and op.mem.base==capstone.x86.X86_REG_RIP:
                note=" ->0x%X"%(ins.address+ins.size+op.mem.disp-IB)
        print("0x%X  %-20s %s %s%s"%(ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str,note))
        n+=1
        if n>=maxn: print("... truncated ..."); break
    print("===== end =====")

for rva,lab in [(0x41EA8B0,"HitTest.BuildAttackMessage"),
                (0x41E7930,"HitTest.HitPointWorld"),
                (0x41E8150,"HitTest.HitNormalWorld"),
                (0x41EFFD0,"HitTest.Clear"),
                (0x579B410,"BaseMelee.DoAttack"),
                (0x57A3240,"BaseMelee.ProcessAttack")]:
    dis(rva,lab)
