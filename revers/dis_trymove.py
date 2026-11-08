import sys, struct
sys.path.insert(0, r"C:\Users\SystemX\Desktop\Rust-Offset-Dumper\tools")
from reverse import Pe
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

DLL = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
pe = Pe(DLL); g = open(DLL, "rb").read()
def rva2off(r):
    for s in pe.sections:
        if s["va"] <= r < s["va"] + s["rawsize"]: return s["raw"] + (r - s["va"])
md = Cs(CS_ARCH_X86, CS_MODE_64)
def dis(rva, n=160):
    o = rva2off(rva)
    for i in md.disasm(g[o:o+n], rva):
        print("  %#x: %-24s %s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))

BASE0 = 0x10E36188
def slot_read(tokidx):
    o = rva2off(BASE0 + tokidx*8)
    return struct.unpack_from("<Q", g, o)[0]
print("TryToMove candidate ordinal102 idx59515 token 0x600e87c RVA", hex((slot_read(0x600e87c & 0xFFFFFF)-0x180000000)))
print("lambda b__0 token 0x600e957 RVA", hex((slot_read(0x600e957 & 0xFFFFFF)-0x180000000)))
print("ctor token 0x600e958 RVA", hex((slot_read(0x600e958 & 0xFFFFFF)-0x180000000)))
print("=== disasm 0x1832980 ===")
dis(0x1832980, 200)
