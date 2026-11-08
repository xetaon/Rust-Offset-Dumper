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
    return None

TYPES = 0xFBA9B30
SIZES = 0x110EF100

def ptr_at(base, idx):
    q = struct.unpack_from("<Q", d, base + idx * 8)[0]
    r = q - IB
    o = r2o(r)
    return o

def type_info(idx):
    o = ptr_at(TYPES, idx)
    data = struct.unpack_from("<Q", d, o)[0]
    bits = struct.unpack_from("<I", d, o + 8)[0]
    return data, (bits >> 16) & 0xFF, bits & 0xFFFF

def size_info(tdi):
    o = ptr_at(SIZES, tdi)
    inst, nat, stat, thr = struct.unpack_from("<IiiI", d, o)
    return inst, nat, stat, thr

PRIM = {0x02: (1, 1), 0x03: (2, 2), 0x04: (1, 1), 0x05: (1, 1),
        0x06: (2, 2), 0x07: (2, 2), 0x08: (4, 4), 0x09: (4, 4),
        0x0A: (8, 8), 0x0B: (8, 8), 0x0C: (4, 4), 0x0D: (8, 8),
        0x18: (8, 8), 0x19: (8, 8)}
REF = {0x0E, 0x0F, 0x12, 0x14, 0x1B, 0x1C, 0x15, 0x1A, 0x13, 0x1D, 0x01}

def fsize(fidx, strategy):
    data, typ, attrs = type_info(fidx)
    if typ in PRIM:
        return PRIM[typ], attrs
    if typ == 0x11:  # valuetype
        inst = size_info(data)[0] if data < md.type_count else 4
        if strategy == "A":
            al = 1
            while al * 2 <= min(inst, 8) and inst % (al * 2) == 0:
                al *= 2
        else:
            al = 8
        return (inst, al), attrs
    return (8, 8), attrs

def align_up(v, a):
    return (v + a - 1) // a * a

def build(strategy="A", final_align=True):
    sizes = {}
    for tdi in range(md.type_count):
        t = md.type(tdi)
        base = 0
        p = t["parent_type"]
        if 0 <= p < md.type_count:
            base = sizes.get(p)
            if base is None:
                base = size_info(p)[0]
        cur = base
        off = md.sections["fields"][0]
        for k in range(t["field_count"]):
            b = off + (t["first_field"] + k) * 12
            ni, fi, tok = struct.unpack_from("<iiI", md.data, b)
            (sz, al), attrs = fsize(fi, strategy)
            if attrs & 0x10:  # static
                continue
            cur = align_up(cur, al)
            cur += sz
        inst = size_info(tdi)[0]
        # class alignment: try 8
        pred = align_up(cur, 8) if final_align else cur
        sizes[tdi] = pred
    return sizes

for strat in ("A",):
    sizes = build(strat)
    ok = bad = 0
    badlist = []
    for tdi in range(md.type_count):
        if sizes[tdi] == size_info(tdi)[0]:
            ok += 1
        else:
            bad += 1
            if len(badlist) < 15:
                badlist.append((tdi, die := size_info(tdi)[0], sizes[tdi]))
    print(strat, "ok", ok, "bad", bad)
    for x in badlist:
        print("   tdi", x[0], md.type(x[0])["name"], "stored", hex(x[1]), "pred", hex(x[2]))
