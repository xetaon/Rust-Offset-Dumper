import sys, struct
sys.path.insert(0, r"C:\Users\SystemX\Desktop\Rust-Offset-Dumper\tools")
import meta_rva as M
d = open(M.DEFAULT_DLL, "rb").read()
pe = M.Pe(M.DEFAULT_DLL)
IB = M.IMAGE_BASE
md = M.Metadata(M.DEFAULT_METADATA)

def r2o(r):
    return pe.rva_to_off(r)

# find structs with instance_size 0x7f8, native -1
cands = []
for secname in (".rdata", ".data"):
    s = next(x for x in pe.sections if x["name"] == secname)
    start, end = s["raw"], s["raw"] + s["rawsize"]
    pat = struct.pack("<i", 0x7f8)
    i = start
    while True:
        i = d.find(pat, i, end)
        if i == -1: break
        if i + 16 <= end:
            inst, nat, st, th = struct.unpack_from("<4i", d, i)
            if nat in (-1, 0xffffffff) and 0 <= st < 0x100000 and th == 0:
                rva = s["va"] + (i - s["raw"])
                cands.append(rva)
        i += 4
print("size struct candidates (0x7f8):", [hex(x) for x in cands[:20]])

def find_bases(struct_rva, index):
    pat = struct.pack("<Q", IB + struct_rva)
    hits = []
    for secname in (".rdata", ".data"):
        s = next(x for x in pe.sections if x["name"] == secname)
        start, end = s["raw"], s["raw"] + s["rawsize"]
        i = start
        while True:
            i = d.find(pat, i, end)
            if i == -1: break
            pos = i - index * 8
            if start <= pos < end:
                hits.append(s["va"] + (pos - s["raw"]))
            i += 1
    return hits

for sr in cands[:6]:
    print(hex(sr), "-> bases", [hex(x) for x in find_bases(sr, 5604)[:10]])

def check(base):
    res = {}
    for tdi, name in ((5604, "BasePlayer"), (8570, "Projectile"), (9199, "AttackEntity"), (7227, "PlayerModel")):
        q = struct.unpack_from("<Q", d, r2o(base + tdi * 8))[0]
        o = r2o(q - IB)
        res[name] = struct.unpack_from("<4i", d, o) if o else None
    return res
for b in (0x110EF100,):
    print("old", hex(b), check(b))
