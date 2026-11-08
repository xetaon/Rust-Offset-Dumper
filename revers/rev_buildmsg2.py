import pefile, capstone
PATH=r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
pe=pefile.PE(PATH,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
DATA=open(PATH,"rb").read()
def off(va): return pe.get_offset_from_rva(va)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64); md.detail=True
rva=0x41EA8B0; n=0xC00
o=off(rva); code=DATA[o:o+n]
import re
seen=[]
for ins in md.disasm(code,IB+rva):
    s="%s %s"%(ins.mnemonic,ins.op_str)
    if re.search(r'\[(rdi|rsi|rbx|r14|r13) \+ 0x[0-9a-f]+\]', s) or ins.mnemonic=="ret":
        print("0x%X  %-22s %s"%(ins.address,ins.bytes.hex(),s))
        if ins.mnemonic=="ret": break
