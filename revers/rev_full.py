import pefile, capstone
PATH=r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
pe=pefile.PE(PATH,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
DATA=open(PATH,"rb").read()
def va2off(va): return pe.get_offset_from_rva(va)
def dis(va,size,label):
    o=va2off(va); code=DATA[o:o+size]
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64); md.detail=True
    print("\n===== %s 0x%X..0x%X ====="%(label,va,va+size))
    for ins in md.disasm(code,IB+va):
        print("0x%X  %-20s %s %s"%(ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str))
    print("===== end =====")
dis(0x1C5C780,0x431,"entity helper")
dis(0x1C5AE20,0x226,"first list-const fn")
