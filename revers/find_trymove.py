import struct, sys
sys.path.insert(0, r"C:\Users\SystemX\AppData\Local\Temp\opencode")
import meta_parse as M

t = M.read_type(2293)
print("ItemIcon type", t)
for mi in range(t["firstMethod"], t["firstMethod"] + t["methodCount"]):
    m = M.read_method(mi)
    if "TryToMove" in (m["name"] or ""):
        print("HIT", m)
# also list names that are odd short and contain TryToMove anywhere
for i in range(M.NM):
    m = M.read_method(i)
    if m["name"] and "TryToMove" in m["name"]:
        tt = M.read_type(m["decl"])
        print("method", i, m["name"], "decl", m["decl"], tt["ns"], tt["name"], "token", hex(m["token"]), "slot", m["slot"], "flags", hex(m["flags"]))
