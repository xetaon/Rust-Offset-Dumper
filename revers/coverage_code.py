import sys, struct, re
from collections import Counter
sys.path.insert(0, r"C:\Users\SystemX\Desktop\Rust-Offset-Dumper\tools")
sys.path.insert(0, r"C:\Users\SystemX\Desktop\Rust-Offset-Dumper\revers")
import meta_rva as M
import rev_classes as RC
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

md = M.Metadata(M.DEFAULT_METADATA)
pe = M.Pe(M.DEFAULT_DLL)
mp = M.RvaMapper(md, pe)
cs = Cs(CS_ARCH_X86, CS_MODE_64); cs.detail = True

REQ = {k: [(n, o) for n, o, _t in v] for k, v in RC.EXPECTED.items()}
# BasePlayer request (from the task list)
bp = []
txt = open(r"C:\Users\SystemX\Desktop\Rust-Offset-Dumper\revers\out\BasePlayer_offsets.h", encoding="utf-8").read()
for m in re.finditer(r"constexpr std::uintptr_t (\w+)\s*=\s*0x([0-9A-Fa-f]+)", txt):
    bp.append((m.group(1), int(m.group(2), 16)))
REQ["BasePlayer"] = bp

STACK = {"rsp", "esp", "rbp", "ebp"}

def tdi_of(nm):
    for i in range(md.type_count):
        if md.type(i)["name"] == nm:
            return i
    return None

def collect(tdi):
    t = md.type(tdi)
    seen = {}
    for k in range(t["method_count"]):
        m = md.method(t["first_method"] + k)
        info = mp.rva_for_method(m)
        if not info:
            continue
        o = pe.rva_to_off(info["rva"])
        if o is None:
            continue
        code = pe.data[o:o + 3000]
        cnt = 0
        for ins in cs.disasm(code, info["rva"]):
            cnt += 1
            if cnt > 900 or ins.mnemonic in ("ret", "int3"):
                break
            for op in ins.operands:
                if op.type == 3 and op.mem.base:
                    d = op.mem.disp
                    if 0x10 <= d <= 0x1000:
                        bn = ins.reg_name(op.mem.base)
                        if bn in STACK:
                            continue
                        seen.setdefault(d, (m["name"], info["rva"], ins.address, ins.mnemonic + " " + ins.op_str))
    return seen

for nm, rows in REQ.items():
    tdi = tdi_of(nm)
    seen = collect(tdi)
    miss = []
    hit = 0
    for f, off in rows:
        if off in seen:
            hit += 1
        else:
            miss.append((f, hex(off)))
    print("%-14s methods=%-4d requested=%-4d seen_in_code=%-4d missing=%d" % (
        nm, md.type(tdi)["method_count"], len(rows), hit, len(miss)))
    if miss:
        print("   MISS", miss)
