import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rev_loot import Pe, DLL
import capstone

pe = Pe(DLL)
funcs = pe.functions()
rva = 0x1834DB0
m = [f for f in funcs if f[0] <= rva < f[1]][0]
b, e = m
print("function 0x%X..0x%X len 0x%X" % (b, e, e-b))
code = pe.read(b, e-b)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
md.detail = True
calls = []
for ins in md.disasm(code, b):
    if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == capstone.x86.X86_OP_IMM:
        calls.append(ins.operands[0].imm)
print("call targets:", " ".join("0x%X" % c for c in sorted(set(calls))))
print("calls 0x185C650:", 0x185C650 in calls)
# find stores/reads of +0x78, +0x160
for ins in md.disasm(code, b):
    if "[rbx + 0x78]" in ins.op_str or "[rbx + 0x160]" in ins.op_str or "+ 0x78]" in ins.op_str and "rbx" in ins.op_str:
        print("0x%08X  %s %s" % (ins.address, ins.mnemonic, ins.op_str))
