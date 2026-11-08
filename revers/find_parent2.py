import sys, struct
sys.path.insert(0, r"C:\Users\SystemX\AppData\Local\Temp\opencode")
sys.path.insert(0, r"C:\Users\SystemX\Desktop\Rust-Offset-Dumper\tools")
import meta_parse as M
from reverse import Pe
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_MEM, X86_REG_RIP

DLL = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
pe = Pe(DLL); g = open(DLL, "rb").read()
secs = {s["name"]: s for s in pe.sections}
def rva2off(r):
    for s in pe.sections:
        if s["va"] <= r < s["va"] + s["rawsize"]: return s["raw"] + (r - s["va"])
pd = secs[".pdata"]; pdata = {}
for i in range(pd["rawsize"]//12):
    b,e,u = struct.unpack_from("<III", g, pd["raw"]+i*12)
    if b: pdata[b]=e
BASE0 = 0x10E36188
def slot_val(t): return struct.unpack_from("<Q", g, rva2off(BASE0+t*8))[0]
def m_rva(t): return slot_val(t)-0x180000000
md = Cs(CS_ARCH_X86, CS_MODE_64); md.detail=True
lam = m_rva(0x600e957 & 0xFFFFFF)
targets = {}
o=rva2off(lam)
for ins in md.disasm(g[o:o+0x120], lam):
    if ins.mnemonic=="lea":
        for op in ins.operands:
            if op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:
                targets[ins.address+ins.size+op.mem.disp]=[]
    if ins.address>lam+0x100: break
print("lambda targets:", [hex(t) for t in targets])
t=M.read_type(2293)
for ordn in range(t["methodCount"]):
    mi=t["firstMethod"]+ordn; m=M.read_method(mi); rva=m_rva(m["token"]&0xFFFFFF)
    end=pdata.get(rva) or (rva+0x400)
    o=rva2off(rva); e=rva2off(end) or o+(end-rva)
    seen=set()
    for ins in md.disasm(g[o:e], rva):
        for op in ins.operands:
            if op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:
                tt=ins.address+ins.size+op.mem.disp
                if tt in targets: seen.add(tt)
    for tt in seen: targets[tt].append((ordn, mi, m["name"], hex(rva)))
for tt,lst in targets.items():
    print("TARGET",hex(tt),"count",len(lst))
    for x in lst[:12]: print("   ",x)
    if len(lst)>12: print("    ...")
