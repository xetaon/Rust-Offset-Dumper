import struct, sys
sys.path.insert(0, r"C:\Users\SystemX\Desktop\Rust-Offset-Dumper\tools")
import meta_rva as M

DLL = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
d = open(DLL, "rb").read()
IB = 0x180000000
md = M.Metadata(M.DEFAULT_METADATA)
SECS = [(0x1000, 0x8e4400, 0x400, 0x8e4400),
        (0x8e6000, 0xe2ce600, 0x8e4800, 0xe2ce600),
        (0xebb5000, 0x20c6800, 0xebb2e00, 0x20c6800),
        (0x10c7c000, 0xa45e00, 0x10c79600, 0xa45e00)]
def r2o(r):
    for va, vs, raw, rs in SECS:
        if va <= r < va + rs:
            return raw + (r - va)
TYPES = 0xFBA9B30
SIZES = 0x110EF100
def ptr(base, i):
    return r2o(struct.unpack_from("<Q", d, base + i * 8)[0] - IB)
def tinfo(i):
    o = ptr(TYPES, i)
    if o is None:
        return None
    return struct.unpack_from("<Q", d, o)[0], (struct.unpack_from("<I", d, o + 8)[0] >> 16) & 0xFF
def sinfo(i):
    o = ptr(SIZES, i)
    return struct.unpack_from("<I", d, o)[0] if o else 0

PRIM = {0x02:(1,1),0x03:(2,2),0x04:(1,1),0x05:(1,1),0x06:(2,2),0x07:(2,2),
        0x08:(4,4),0x09:(4,4),0x0A:(8,8),0x0B:(8,8),0x0C:(4,4),0x0D:(8,8),
        0x18:(8,8),0x19:(8,8)}
REF = {0x0E,0x0F,0x12,0x14,0x1A,0x1B,0x1C,0x13,0x1D,0x15,0x01}
def fsize(fi):
    data, typ = tinfo(fi)
    if typ in PRIM:
        return PRIM[typ]
    if typ == 0x11:
        inst = sinfo(data)
        al = 1
        while al * 2 <= min(inst, 8) and inst % (al * 2) == 0:
            al *= 2
        return inst, al
    return 8, 8
def au(v, a):
    return (v + a - 1) // a * a

def class_base(tdi, cache):
    p = md.type(tdi)["parent_type"]
    if p < 0:
        return 0
    ti = tinfo(p)
    if ti is None:
        return 0
    data, typ = ti
    if typ == 0x12 or typ == 0x11:
        return layout(data, cache)[0]
    if typ == 0x15:  # generic inst -> try data as class
        return 8
    return 0

def layout(tdi, cache):
    if tdi in cache:
        return cache[tdi]
    t = md.type(tdi)
    cur = class_base(tdi, cache)
    off = md.sections["fields"][0]
    fl = []
    for k in range(t["field_count"]):
        b = off + (t["first_field"] + k) * 12
        ni, fi, tok = struct.unpack_from("<iiI", md.data, b)
        data, typ = tinfo(fi)
        attrs = struct.unpack_from("<I", d, ptr(TYPES, fi) + 8)[0] & 0xFFFF
        if attrs & 0x10:
            continue
        sz, al = fsize(fi)
        cur = au(cur, al)
        fl.append((k, md.string(ni), cur, sz, typ, attrs))
        cur += sz
    cache[tdi] = (cur, fl)
    return cache[tdi]

cache = {}
ok = bad = 0
badl = []
for tdi in range(md.type_count):
    pred = layout(tdi, cache)[0]
    st = sinfo(tdi)
    if pred == st:
        ok += 1
    else:
        bad += 1
        if len(badl) < 20:
            badl.append((tdi, md.type(tdi)["name"], st, pred))
print("ok", ok, "bad", bad)
for x in badl:
    print("  tdi", x[0], x[1], "stored", hex(x[2]), "pred", hex(x[3]))
for name in ("BasePlayer", "Projectile", "AttackEntity", "PlayerModel"):
    for i in range(md.type_count):
        if md.type(i)["name"] == name:
            print(name, "stored", hex(sinfo(i)), "pred", hex(layout(i, cache)[0]))
            break
