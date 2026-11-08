import sys, struct
sys.path.insert(0, r"C:\Users\SystemX\Desktop\Rust-Offset-Dumper\tools")
from reverse import Pe
DLL = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
pe = Pe(DLL); d = open(DLL, "rb").read()
def rva2off(r):
    for s in pe.sections:
        if s["va"] <= r < s["va"] + s["rawsize"]: return s["raw"] + (r - s["va"])
def off2rva(o):
    for s in pe.sections:
        if s["raw"] <= o < s["raw"] + s["rawsize"]: return s["va"] + (o - s["raw"])
def slot_val(slot):
    o = rva2off(slot)
    if o is None: return None
    v = struct.unpack_from("<Q", d, o)[0]
    return v
BASE = 0x10E36188
for name, tok in [("PerfUpdate",0x192), ("LootOnClicked",0x2a4dc), ("LootAwake",0x2a4de), ("DevOnGUI",0x2863b), ("Cursor",0x35ced), ("Projectile",0x3a191)]:
    slot = BASE + tok*8
    v = slot_val(slot)
    print("%-14s slot=%#x val=%#x rva=%#x" % (name, slot, v or 0, (v-0x180000000) if v else 0))
print("--- around PerfUpdate slot ---")
for k in range(-6, 7):
    tok = 0x192 + k; slot = BASE + tok*8; v = slot_val(slot)
    print("tokidx %#x (%d) slot %#x -> %#x" % (tok, tok, slot, (v-0x180000000) if v else 0))
print("--- around 0x110ADD78 ---")
for k in range(-8, 9):
    slot = 0x110ADD78 + k*8; v = slot_val(slot)
    print("slot %#x -> %#x" % (slot, (v-0x180000000) if v else 0))
# find start of contiguous valid ptr run around 0x110ADD78
def isptr(v): return 0x180000000 < v < 0x180000000+0x121f4600
o = rva2off(0x110ADD78)
start = o
while start-8 >= 0 and isptr(struct.unpack_from("<Q", d, start-8)[0]): start -= 8
end = o
while end+8 < len(d) and isptr(struct.unpack_from("<Q", d, end+8)[0]): end += 8
print("run 0x110ADD78: %#x..%#x count=%d startidx=%d" % (off2rva(start), off2rva(end), (end-start)//8+1, (off2rva(start)-BASE)//8))
