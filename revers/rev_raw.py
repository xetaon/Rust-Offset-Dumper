import pefile, capstone
PATH=r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
pe=pefile.PE(PATH,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
DATA=open(PATH,"rb").read()
def off(va): return pe.get_offset_from_rva(va)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64); md.detail=True
def raw(rva,n,label):
    o=off(rva); code=DATA[o:o+n]
    print("\n--- %s RVA 0x%X (%d bytes) ---"%(label,rva,n))
    for ins in md.disasm(code,IB+rva):
        note=""
        for op in ins.operands:
            if op.type==capstone.x86.X86_OP_MEM and op.mem.base==capstone.x86.X86_REG_RIP:
                note=" ->0x%X"%(ins.address+ins.size+op.mem.disp-IB)
        print("0x%X  %-20s %s %s%s"%(ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str,note))
raw(0x41EA9E0,0x120,"after BuildAttackMessage pdata end")
raw(0x41EA970,0x90,"guard target region")
