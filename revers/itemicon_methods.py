import sys, struct
sys.path.insert(0, r"C:\Users\SystemX\AppData\Local\Temp\opencode")
import meta_parse as M
sys.path.insert(0, r"C:\Users\SystemX\Desktop\Rust-Offset-Dumper\tools")
from reverse import Pe

DLL = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
pe = Pe(DLL); g = open(DLL, "rb").read()
def rva2off(r):
    for s in pe.sections:
        if s["va"] <= r < s["va"] + s["rawsize"]: return s["raw"] + (r - s["va"])
def method_rva(native_tokidx, base):
    slot = base + native_tokidx*8
    o = rva2off(slot)
    if o is None: return None, slot
    v = struct.unpack_from("<Q", g, o)[0]
    return (v - 0x180000000) if v else None, slot

BASE0 = 0x10E36188
t = M.read_type(2293)
print("ItemIcon first", t["firstMethod"], "count", t["methodCount"])
for ordn in range(t["methodCount"]):
    mi = t["firstMethod"] + ordn
    m = M.read_method(mi)
    tokidx = m["token"] & 0xFFFFFF
    rva, slot = method_rva(tokidx, BASE0)
    nm = m["name"] or ""
    mark = " <<<<<" if ordn in (100,101,102,103,104) else ""
    print("%3d idx=%6d tok=%#x rva=%#x p=%d flags=%#04x name=%s%s" % (ordn, mi, m["token"], rva or 0, m["paramCount"], m["flags"], nm[:46], mark))
