import sys, struct
sys.path.insert(0, r"C:\Users\SystemX\Desktop\Rust-Offset-Dumper\tools")
from reverse import Pe
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

DLL = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
pe = Pe(DLL); g = open(DLL, "rb").read()
def rva2off(r):
    for s in pe.sections:
        if s["va"] <= r < s["va"] + s["rawsize"]: return s["raw"] + (r - s["va"])
def off2rva(o):
    for s in pe.sections:
        if s["raw"] <= o < s["raw"] + s["rawsize"]: return s["va"] + (o - s["raw"])
md = Cs(CS_ARCH_X86, CS_MODE_64)
def dis(rva, n=120):
    o = rva2off(rva)
    for i in md.disasm(g[o:o+n], rva):
        print("  %#x: %-20s %s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
        if i.address > rva + n: break

LAMBDA = 0x180185c650
pat = struct.pack("<Q", LAMBDA)
hits = []
st = 0
while True:
    i = g.find(pat, st)
    if i < 0: break
    hits.append(off2rva(i)); st = i+1
print("lambda ptr 0x%x hits:" % LAMBDA, [hex(h) for h in hits])
print("=== disasm ctor 0x8ea3d0 ===")
dis(0x8ea3d0, 80)
print("=== disasm lambda 0x185c650 ===")
dis(0x185c650, 160)
# print struct dwords around each hit
for h in hits:
    o = rva2off(h)
    print("--- around", hex(h))
    for k in range(-4, 12):
        v = struct.unpack_from("<Q", g, o+k*8)[0]
        print("   %+d %#x: %#018x" % (k, h+k*8, v))
