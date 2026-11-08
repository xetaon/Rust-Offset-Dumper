import sys, struct
sys.path.insert(0, r"C:\Users\SystemX\Desktop\Rust-Offset-Dumper\tools")
import meta_rva as M
d = open(M.DEFAULT_DLL, "rb").read()
md = M.Metadata(M.DEFAULT_METADATA)

TYPES = 0xFBA9B30
def r2o(r):
    return M.Pe(M.DEFAULT_DLL).rva_to_off(r) if False else None
pe = M.Pe(M.DEFAULT_DLL)
def tinfo(i):
    o = pe.rva_to_off(struct.unpack_from("<Q", d, TYPES + i*8)[0] - M.IMAGE_BASE)
    if o is None: return None
    return struct.unpack_from("<Q", d, o)[0], (struct.unpack_from("<I", d, o+8)[0] >> 16) & 0xff, struct.unpack_from("<I", d, o+8)[0] & 0xffff

def dump(nm, base):
    tdi = [i for i in range(md.type_count) if md.type(i)["name"] == nm][0]
    t = md.type(tdi)
    fo = md.sections["fields"][0]
    print("===", nm, "tdi", tdi, "fields", t["field_count"], "table", hex(base) if base else None)
    for k in range(t["field_count"]):
        b = fo + (t["first_field"] + k)*12
        ni, fi, tok = struct.unpack_from("<iiI", md.data, b)
        name = md.string(ni)
        x = tinfo(fi)
        typ, attrs = (x[1], x[2]) if x else (0, 0)
        val = struct.unpack_from("<i", d, pe.rva_to_off(base) + 4*k)[0] if base else None
        print(" %3d %-32s ty=%#04x at=%#06x tbl=%s" % (
            k, (name or "")[:32], typ, attrs,
            "POISON" if val == 0x67676767 else (hex(val) if val is not None else "?")))

dump("AttackEntity", 0xEC4E6D0)
dump("Projectile", 0xEC2ED00)
dump("BasePlayer", None)
dump("PlayerModel", None)

