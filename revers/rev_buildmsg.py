import pefile, capstone, re
PATH=r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
pe=pefile.PE(PATH,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
DATA=open(PATH,"rb").read()
def off(va): return pe.get_offset_from_rva(va)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64); md.detail=True
rva=0x41EA8B0; n=0x520
o=off(rva); code=DATA[o:o+n]
print("BuildAttackMessage body 0x%X..0x%X"%(rva,rva+n))
for ins in md.disasm(code,IB+rva):
    # only print instrs with mem operand using rdi/rsi/rbx + disp, or calls
    s="%s %s"%(ins.mnemonic,ins.op_str)
    if ("rdi +" in s) or ("rsi +" in s) or ("rbx +" in s) or ins.mnemonic=="call" or ins.mnemonic=="ret":
        print("0x%X  %-22s %s"%(ins.address,ins.bytes.hex(),s))
