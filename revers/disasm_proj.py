import sys, struct
from collections import Counter
sys.path.insert(0, r"C:\Users\SystemX\Desktop\Rust-Offset-Dumper\tools")
import meta_rva as M
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

md = M.Metadata(M.DEFAULT_METADATA)
pe = M.Pe(M.DEFAULT_DLL)
mp = M.RvaMapper(md, pe)
md_cs = Cs(CS_ARCH_X86, CS_MODE_64)
md_cs.detail = True

def cls(nm):
    return [i for i in range(md.type_count) if md.type(i)["name"] == nm][0]

def meths(tdi):
    t = md.type(tdi)
    out = []
    for k in range(t["method_count"]):
        m = md.method(t["first_method"] + k)
        info = mp.rva_for_method(m)
        if info:
            out.append((m, info["rva"]))
    return out

def scan(nm, want):
    tdi = cls(nm)
    print("===", nm, "methods", md.type(tdi)["method_count"])
    hist = Counter()
    examples = {}
    for m, rva in meths(tdi):
        o = pe.rva_to_off(rva)
        if o is None:
            continue
        code = pe.data[o:o + 1200]
        n = 0
        for ins in md_cs.disasm(code, rva):
            n += 1
            if n > 400:
                break
            if ins.mnemonic in ("ret", "int3"):
                break
            for op in ins.operands:
                if op.type == 3 and op.mem.base != 0:  # X86_OP_MEM
                    d = op.mem.disp
                    if 0x20 <= d <= 0x900:
                        hist[d] += 1
                        examples.setdefault(d, (m["name"], rva, ins.address, ins.mnemonic + " " + ins.op_str))
    print("  distinct disps", len(hist))
    for w in want:
        c = hist.get(w, 0)
        print("   want %#5x -> %d %s" % (w, c, examples.get(w)))
    top = hist.most_common(30)
    print("  top:", [(hex(k), v) for k, v in top])

scan("Projectile", [0x28,0x34,0x38,0x40,0x44,0x48,0x54,0x58,0x98,0xa0,0x120,0x128,0x140,0x164,0x170,0x17c,0x180,0x188,0x194,0x1a0,0x1ac,0x1e0,0x1f0])
