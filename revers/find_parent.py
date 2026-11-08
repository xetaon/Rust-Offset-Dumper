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
    return None
# .pdata
pd = secs[".pdata"]
pdata = {}
for i in range(pd["rawsize"]//12):
    b, e, u = struct.unpack_from("<III", g, pd["raw"] + i*12)
    if b: pdata[b] = e
print("pdata funcs", len(pdata))

BASE0 = 0x10E36188
def slot_rva(tokidx): return BASE0 + tokidx*8
def slot_val(tokidx):
    o = rva2off(slot_rva(tokidx)); return struct.unpack_from("<Q", g, o)[0]
def m_rva(tokidx): return slot_val(tokidx) - 0x180000000

# compute the 4 lea targets in lambda body robustly with capstone
md = Cs(CS_ARCH_X86, CS_MODE_64); md.detail = True
lam_rva = m_rva(0x600e957 & 0xFFFFFF)
print("lambda rva", hex(lam_rva))
targets = set()
o = rva2off(lam_rva)
for ins in md.disasm(g[o:o+0x120], lam_rva):
    if ins.mnemonic in ("lea","mov"):
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                targets.add(t)
    if ins.address > lam_rva + 0x100: break
print("rip targets in lambda:", [hex(t) for t in targets])

# enumerate ItemIcon methods and their RVAs
t = M.read_type(2293)
methods = []
for ordn in range(t["methodCount"]):
    mi = t["firstMethod"] + ordn
    m = M.read_method(mi)
    rva = m_rva(m["token"] & 0xFFFFFF)
    methods.append((ordn, mi, m, rva))
print("itemicon methods", len(methods))

found = []
for ordn, mi, m, rva in methods:
    end = pdata.get(rva)
    if not end:
        # try next method start as bound
        end = rva + 0x200
    o = rva2off(rva)
    if o is None: continue
    code = g[o: rva2off(end) if rva2off(end) else o+ (end-rva)]
    for ins in md.disasm(code, rva):
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                tt = ins.address + ins.size + op.mem.disp
                if tt in targets:
                    found.append((ordn, mi, m["name"], hex(rva), hex(ins.address), ins.mnemonic, ins.op_str, hex(tt)))
                    break
for f in found:
    print("REF", f)
print("total refs", len(found))
