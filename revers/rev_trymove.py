import os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rev_loot import Pe, DLL
import capstone

pe = Pe(DLL)
funcs = pe.functions()
for rva in [0x1834DB0, 0x185C650]:
    m = [f for f in funcs if f[0] <= rva < f[1]]
    if not m:
        print("0x%X not in .pdata" % rva); continue
    b, e = m[0]
    print("\n=== 0x%X..0x%X len 0x%X ===" % (b, e, e-b))
    code = pe.read(b, min(e-b, 0x180))
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    for ins in md.disasm(code, b):
        print("0x%08X  %-20s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
        if ins.address > b + 0x100: break
