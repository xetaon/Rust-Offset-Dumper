"""
Rust-Offset-Dumper static reverser.

* parses GameAssembly.dll (PE, .pdata function bounds)
* finds every "two-word / unrolled cipher block" by symbolic execution
* matches them against the decryptor table that src/Il2Cpp.h used to hardcode
* reports which ones still match the binary and which are stale
* emits src/generated/Decryptors.generated.h with the REAL chains

Usage:
    py tools/reverse.py                 # scan + verify + generate
    py tools/reverse.py --known-only    # no cipher census (fast)
"""
from __future__ import annotations

import bisect
import json
import os
import re
import struct
import sys

import capstone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "out")
GEN = os.path.join(ROOT, "src", "generated")
GAME = r"C:\Program Files (x86)\Steam\steamapps\common\Rust"
DLL = os.path.join(GAME, "GameAssembly.dll")

# name -> (constants in execution order, wrapper_based, expected chain)
# expected chain uses "rol"/"ror" and the same immediates src/Il2Cpp.h used.
KNOWN = {
    "ClientEntitiesDecrypt": (
        [0x49F666DD, 0x0165993A, 0x06EA51C6], True,
        [("sub", 0x49F666DD), ("xor", 0x0165993A), ("rol", 12), ("xor", 0x06EA51C6)]),
    "EntityListDecrypt": (
        [0x606A395C, 0x380CDD1C], True,
        [("add", 0x606A395C), ("rol", 17), ("sub", 0x380CDD1C)]),
    "PlayerEyesDecrypt": (
        [0x8D1FB868, 0xBD80150D, 0x5AA25993], True,
        [("xor", 0x8D1FB868), ("rol", 13), ("xor", 0xBD80150D), ("add", 0x5AA25993)]),
    "PlayerInventoryDecrypt": (
        [0xA0EB8D31, 0x133B75FC], True,
        [("rol", 2), ("add", 0xA0EB8D31), ("rol", 31), ("sub", 0x133B75FC)]),
    "ClActiveItemDecrypt": (
        [0xEC201AFB, 0x3D62F8BA], False,
        [("rol", 2), ("xor", 0xEC201AFB), ("add", 0x3D62F8BA), ("rol", 16)]),
    "UserIDDecrypt": (
        [0x37ED3E45], False,
        [("rol", 26), ("add", 0x37ED3E45), ("rol", 28)]),
    "PlayerWalkMovementBody": (
        [0x2D8A92D2, 0x5D467F75], True,
        [("add", 0x2D8A92D2), ("rol", 27), ("sub", 0x5D467F75), ("rol", 10)]),
    "PlayerWalkMovementCapsule": (
        [0x29260396, 0x3EBF0DEF, 0x4E1F5E20], True,
        [("add", 0x29260396), ("xor", 0x3EBF0DEF), ("add", 0x4E1F5E20)]),
    "BasePlayerCapsuleCollider": (
        [0x7715BC77], True,
        [("rol", 18), ("sub", 0x7715BC77), ("rol", 17)]),
}

U16 = lambda b, o: struct.unpack_from("<H", b, o)[0]
U32 = lambda b, o: struct.unpack_from("<I", b, o)[0]

REG32 = {
    "eax", "ebx", "ecx", "edx", "esi", "edi", "ebp", "esp",
    "r8d", "r9d", "r10d", "r11d", "r12d", "r13d", "r14d", "r15d",
}
X86_REG = capstone.x86.X86_OP_REG
X86_MEM = capstone.x86.X86_OP_MEM
X86_IMM = capstone.x86.X86_OP_IMM
X86_INS_MOV = capstone.x86.X86_INS_MOV
X86_INS_LEA = capstone.x86.X86_INS_LEA


def u32b(v):
    return v & 0xFFFFFFFF


# ===========================================================================
#  PE
# ===========================================================================
class Pe:
    def __init__(self, path):
        with open(path, "rb") as f:
            self.data = f.read()
        d = self.data
        pe = U32(d, 0x3C)
        nsec = U16(d, pe + 6)
        opt = pe + 24
        st = opt + U16(d, pe + 20)
        self.sections = []
        for i in range(nsec):
            o = st + i * 40
            self.sections.append(dict(
                name=d[o:o + 8].rstrip(b"\0").decode("latin1"),
                vsize=U32(d, o + 8), va=U32(d, o + 12),
                rawsize=U32(d, o + 16), raw=U32(d, o + 20),
                chars=U32(d, o + 36)))
        self.size_of_image = U32(d, opt + 56)
        dd = opt + (112 if U16(d, opt) == 0x20B else 96)
        self.dir = [struct.unpack_from("<II", d, dd + i * 8) for i in range(16)]
        self._funcs = None
        self._begins = None

    def rva2off(self, rva):
        for s in self.sections:
            if s["va"] <= rva < s["va"] + max(s["vsize"], s["rawsize"]):
                return s["raw"] + (rva - s["va"])
        return None

    @property
    def exec_sections(self):
        return [s for s in self.sections if s["chars"] & 0x20000000]

    def functions(self):
        if self._funcs is not None:
            return self._funcs
        rva, size = self.dir[3]
        out = []
        off = self.rva2off(rva) if rva else None
        if off is not None:
            for i in range(size // 12):
                b, e, _u = struct.unpack_from("<III", self.data, off + i * 12)
                if b and e > b:
                    out.append((b, e))
        out.sort()
        self._funcs = out
        self._begins = [f[0] for f in out]
        return out

    def func_of(self, rva):
        if self._funcs is None:
            self.functions()
        i = bisect.bisect_right(self._begins, rva) - 1
        if i < 0:
            return None
        b, e = self._funcs[i]
        return (b, e) if b <= rva < e else None

    def function_bytes(self, f):
        b, e = f
        off = self.rva2off(b)
        return self.data[off:off + (e - b)]


# ===========================================================================
#  symbolic word evaluation
# ===========================================================================
class Expr:
    """tiny expression tree, rendered to C++"""
    __slots__ = ("op", "a", "b", "k")

    def __init__(self, op, a=None, b=None, k=None):
        self.op, self.a, self.b, self.k = op, a, b, k

    def cpp(self):
        op, a, b, k = self.op, self.a, self.b, self.k
        A = a.cpp() if isinstance(a, Expr) else str(a)
        B = b.cpp() if isinstance(b, Expr) else str(b)
        if op == "var":
            return "v"
        if op == "const":
            return f"0x{k:08X}u"
        if op in ("+", "-", "^", "|", "&"):
            return f"({A} {op} {B})"
        if op in ("<<", ">>"):
            return f"((u32)({A}) {op} {k})"
        if op == "rol":
            return f"(((u32)({A}) << {k}) | ((u32)({A}) >> (32 - {k})))"
        if op == "ror":
            return f"(((u32)({A}) >> {k}) | ((u32)({A}) << (32 - {k})))"
        if op == "~":
            return f"(~((u32)({A})))"
        if op == "bswap":
            return f"(_byteswap_ulong((u32)({A})))"
        return A


def _same_expr(a, b):
    if not isinstance(a, Expr) or not isinstance(b, Expr):
        return False
    if a.op != b.op:
        return False
    if a.op == "var":
        return True
    if a.op == "const":
        return a.k == b.k
    if a.k != b.k:
        return False
    return _same_expr(a.a, b.a) and _same_expr(a.b, b.b)


class Sim:
    """runs one dword through the cipher block"""

    def __init__(self, md):
        self.md = md
        self.regs = {}
        self.chain = []
        self.result = None
        self.words = 1

    def reg(self, op):
        return self.md.reg_name(op.reg)

    def copy_state(self, other):
        self.regs = dict(other.regs)
        self.chain = other.chain

    def run(self, body):
        for ins in body:
            if self.result is not None:
                break
            self.step(ins)
        return self.result

    def step(self, ins):
        m, ops = ins.mnemonic, ins.operands
        if m == "mov" and len(ops) == 2:
            d, s = ops
            if d.type == X86_REG and self.reg(d) in REG32:
                if s.type == X86_REG and self.reg(s) in REG32:
                    self.regs[self.reg(d)] = self.regs.get(self.reg(s))
                elif s.type == X86_IMM:
                    self.regs[self.reg(d)] = Expr("const", k=u32b(s.imm))
                else:
                    # keep a pre-seeded `v` when the second half of a rotation
                    # loads the same dword into another register
                    if self.regs.get(self.reg(d)) is None:
                        self.regs[self.reg(d)] = None
            elif d.type == X86_MEM and s.type == X86_REG and self.reg(s) in REG32:
                e = self.regs.get(self.reg(s))
                if e is not None:
                    self.result = e
            return
        if m == "lea":
            if ops and ops[0].type == X86_REG and self.reg(ops[0]) in REG32:
                self.regs[self.reg(ops[0])] = None
            return
        if m == "not" and ops and ops[0].type == X86_REG and self.reg(ops[0]) in REG32:
            r = self.reg(ops[0])
            e = self.regs.get(r)
            if e is not None:
                self.regs[r] = Expr("~", a=e)
                self.chain.append(("not", None))
            return
        if m == "bswap" and ops and ops[0].type == X86_REG and self.reg(ops[0]) in REG32:
            r = self.reg(ops[0])
            e = self.regs.get(r)
            if e is not None:
                self.regs[r] = Expr("bswap", a=e)
                self.chain.append(("bswap", None))
            return
        if m not in ("add", "sub", "xor", "or", "and", "shl", "shr", "sar", "rol", "ror"):
            return
        if len(ops) != 2 or ops[0].type != X86_REG or self.reg(ops[0]) not in REG32:
            return
        r = self.reg(ops[0])
        cur = self.regs.get(r)
        if cur is None:
            return
        s = ops[1]
        if s.type == X86_IMM:
            rhs = Expr("const", k=u32b(s.imm))
            imm = u32b(s.imm)
        elif s.type == X86_REG and self.reg(s) in REG32:
            rhs = self.regs.get(self.reg(s))
            imm = None
        else:
            self.regs[r] = None
            return
        if rhs is None:
            self.regs[r] = None
            return

        if m in ("add", "sub", "xor", "or", "and"):
            self.regs[r] = Expr({"add": "+", "sub": "-", "xor": "^", "or": "|", "and": "&"}[m],
                                a=cur, b=rhs)
            self.chain.append((m, imm))
        elif m == "shl":
            self.regs[r] = Expr("<<", a=cur, k=imm)
            self.chain.append(("shl", imm))
        elif m in ("shr", "sar"):
            self.regs[r] = Expr(">>", a=cur, k=imm)
            self.chain.append(("shr", imm))
        elif m in ("rol", "ror"):
            self.regs[r] = Expr(m, a=cur, k=imm)
            self.chain.append((m, imm))
            # fuse explicit shl/shr + or into a rotation
            self._fuse_rotation()

    def _fuse_rotation(self):
        pass


def normalize_chain(chain):
    """collapse (shl n)(shr m)(or) triples into rol/ror where n+m==32"""
    out = []
    i = 0
    while i < len(chain):
        op, imm = chain[i]
        if op in ("shl", "shr") and imm is not None and i + 2 < len(chain) \
           and chain[i + 1][0] in ("shl", "shr") and chain[i + 1][1] is not None \
           and chain[i + 2][0] == "or" and chain[i + 1][0] != op:
            a, b = chain[i], chain[i + 1]
            if a[1] + b[1] == 32:
                n = a[1] if a[0] == "shl" else b[1]
                out.append(("rol", n))
                i += 3
                continue
        out.append((op, imm))
        i += 1
    return out


def invert_chain(chain):
    """inverse of a reversible chain (add<->sub, rol<->ror, xor) or None"""
    out = []
    for op, imm in reversed(chain):
        if op == "add":
            out.append(("sub", imm))
        elif op == "sub":
            out.append(("add", imm))
        elif op == "xor":
            out.append(("xor", imm))
        elif op == "rol":
            out.append(("rol", (32 - imm) % 32))
        elif op == "ror":
            out.append(("ror", (32 - imm) % 32))
        else:
            return None
    return out


def extract_blocks(md, code, base, max_insn=400):
    """every dword cipher block in the code: symbolic run from a 32-bit load
    to the matching 32-bit store. Returns list of dicts."""
    try:
        insns = list(md.disasm(code, base))
    except capstone.CsError:
        return []
    insns = insns[:max_insn]

    def memkey(op):
        m = op.mem
        return (m.base, m.index, m.disp, op.size)

    blocks = []
    for i, ins in enumerate(insns):
        if ins.mnemonic != "mov" or len(ins.operands) != 2:
            continue
        d, s = ins.operands
        if not (d.type == X86_REG and md.reg_name(d.reg) in REG32):
            continue
        if not (s.type == X86_MEM and s.size == 4):
            continue
        sim = Sim(md)
        sim.regs[md.reg_name(d.reg)] = Expr("var")
        # a rotation often loads the same dword into two registers:
        #   mov ecx,[rdx] / mov eax,[rdx] / shr ecx,30 / shl eax,2 / or eax,ecx
        for nxt in insns[i + 1:i + 5]:
            if nxt.mnemonic == "mov" and len(nxt.operands) == 2:
                d2, s2 = nxt.operands
                if d2.type == X86_REG and md.reg_name(d2.reg) in REG32 \
                   and s2.type == X86_MEM and s2.size == 4 and memkey(s2) == memkey(s):
                    sim.regs[md.reg_name(d2.reg)] = Expr("var")
        sim.run(insns[i + 1:i + 1 + 48])
        if sim.result is None or not sim.chain:
            continue
        blocks.append(dict(start=ins.address,
                           expr=sim.result.cpp(),
                           chain=normalize_chain(sim.chain),
                           raw_chain=sim.chain))
    return blocks


# ===========================================================================
#  function discovery
# ===========================================================================
def functions_with_const(pe, c):
    """all functions whose bytes contain imm32 c"""
    pat = struct.pack("<I", c)
    out = set()
    for s in pe.exec_sections:
        blob = pe.data[s["raw"]:s["raw"] + s["rawsize"]]
        pos = 0
        while True:
            i = blob.find(pat, pos)
            if i < 0:
                break
            rva = s["va"] + i
            f = pe.func_of(rva)
            if f:
                out.add(f)
            pos = i + 1
    return out


def chain_consts(chain):
    return sorted(imm for op, imm in chain if imm is not None)


def main():
    args = set(sys.argv[1:])
    known_only = "--known-only" in args
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(GEN, exist_ok=True)

    pe = Pe(DLL)
    funcs = pe.functions()
    print(f"[+] GameAssembly: {len(pe.data)} bytes, {len(funcs)} functions (.pdata)")

    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True

    def similarity(chain, expected):
        if [list(x) for x in chain] == [list(x) for x in expected]:
            return 10000
        n = min(len(chain), len(expected))
        same = sum(1 for a, b in zip(chain, expected) if list(a) == list(b))
        return same * 10 - abs(len(chain) - len(expected))

    results = []
    for name, (consts, wrapper, expected) in KNOWN.items():
        sets = [functions_with_const(pe, c) for c in consts]
        common = set.intersection(*sets) if sets else set()
        ordered = []      # constants appear in the decrypt direction
        unordered = []    # fallback
        for f in sorted(common, key=lambda x: x[1] - x[0]):
            code = pe.function_bytes(f)
            if len(code) > 0x8000:
                continue
            for b in extract_blocks(md, code, f[0]):
                imm = chain_consts(b["chain"])
                if not all(c in imm for c in consts):
                    continue
                seq = [i for op, i in b["chain"]
                       if op in ("add", "sub", "xor") and i in consts]
                item = (similarity(b["chain"], expected), f, b)
                (ordered if seq == consts else unordered).append(item)
        pool = ordered or unordered
        best = max(pool, key=lambda t: t[0]) if pool else None
        cand = blocks = None
        if best:
            _, cand, blocks = best
        direct = blocks is not None and [list(x) for x in blocks["chain"]] == \
            [list(x) for x in expected]
        inv = invert_chain(expected)
        inv_match = blocks is not None and inv is not None and \
            [list(x) for x in blocks["chain"]] == [list(x) for x in inv]
        decrypt_chain = blocks and [list(x) for x in
                                    (blocks["chain"] if direct else expected if inv_match
                                     else blocks["chain"])]
        item = dict(name=name, wrapper=wrapper,
                    consts=[hex(c) for c in consts],
                    expected=[list(x) for x in expected],
                    func_rva=cand and cand[0],
                    func_end=cand and cand[1],
                    block_rva=blocks and blocks["start"],
                    expr=blocks and blocks["expr"],
                    chain=blocks and [list(x) for x in blocks["chain"]],
                    decrypt_chain=decrypt_chain,
                    direction="direct" if direct else "inverse" if inv_match else "stale",
                    match=direct or inv_match)
        results.append(item)
        if cand:
            status = "MATCH" if direct else "INV" if inv_match else "STALE"
            print(f"[{status:5s}] {name:28s} func=0x{cand[0]:X} block=0x{blocks['start']:X}")
            print(f"         binary: {item['chain']}")
            print(f"         header: {[list(x) for x in expected]}")
        else:
            print(f"[MISS ] {name}: no cipher block with those constants")

    # ---- cipher census ---------------------------------------------------
    census = []
    if not known_only:
        seen = set()
        for it in results:
            if it["func_rva"]:
                seen.add((it["func_rva"], it["block_rva"]))
        for (b, e) in funcs:
            if not (0x40 <= e - b <= 0x1200):
                continue
            code = pe.function_bytes((b, e))
            for blk in extract_blocks(md, code, b):
                if (b, blk["start"]) in seen:
                    continue
                c = chain_consts(blk["chain"])
                if len(c) < 2:
                    continue
                census.append(dict(func_rva=b, func_end=e, block_rva=blk["start"],
                                   chain=[list(x) for x in blk["chain"]],
                                   expr=blk["expr"]))
        print(f"[+] cipher census: {len(census)} blocks outside the known table")

    payload = dict(dll=DLL, size=len(pe.data), known=results, census=census)
    with open(os.path.join(OUT, "decryptors.json"), "w") as f:
        json.dump(payload, f, indent=2)

    # ---- report -----------------------------------------------------------
    lines = ["Rust-Offset-Dumper static decryptor report", "=" * 66,
             f"binary: {DLL}", ""]
    for it in results:
        lines.append(f"{it['name']}  wrapper={it['wrapper']}  "
                     f"{'MATCH' if it['match'] else 'STALE/MISS'}")
        lines.append(f"  func  = {it['func_rva'] and hex(it['func_rva'])}")
        lines.append(f"  block = {it['block_rva'] and hex(it['block_rva'])}")
        lines.append(f"  binary chain = {it['chain']}")
        lines.append(f"  header chain = {it['expected']}")
        lines.append(f"  expr = {it['expr']}")
        lines.append("")
    with open(os.path.join(OUT, "decryptors.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # ---- generated C++ ----------------------------------------------------
    def emit_word(chain):
        out = []
        for op, imm in chain:
            if op == "add":
                out.append(f"        v = (unsigned int)(v + 0x{imm:08X}u);")
            elif op == "sub":
                out.append(f"        v = (unsigned int)(v - 0x{imm:08X}u);")
            elif op == "xor":
                out.append(f"        v = (unsigned int)(v ^ 0x{imm:08X}u);")
            elif op == "and":
                out.append(f"        v = (unsigned int)(v & 0x{imm:08X}u);")
            elif op == "or":
                out.append(f"        v = (unsigned int)(v | 0x{imm:08X}u);")
            elif op == "rol":
                out.append(f"        v = (unsigned int)((v << {imm}) | (v >> (32 - {imm})));")
            elif op == "ror":
                out.append(f"        v = (unsigned int)((v >> {imm}) | (v << (32 - {imm})));")
            elif op == "shl":
                out.append(f"        v = (unsigned int)(v << {imm});")
            elif op == "shr":
                out.append(f"        v = (unsigned int)(v >> {imm});")
            elif op == "not":
                out.append("        v = (unsigned int)(~v);")
            elif op == "bswap":
                out.append("        v = _byteswap_ulong(v);")
        return out

    g = ["// ===========================================================================",
         "//  Decryptors.generated.h  -  AUTO-GENERATED by tools/reverse.py",
         "//",
         "//  Every chain below was recovered from GameAssembly.dll by symbolic",
         "//  execution of the real cipher block - not typed in by hand.",
         "//  DO NOT EDIT. Re-run:  py tools/reverse.py",
         "// ===========================================================================",
         "#pragma once", "", "namespace generated", "{"]
    for it in results:
        if not it["decrypt_chain"]:
            continue
        note = {"direct": "binary == header", "inverse": "binary is the encryptor, header is its inverse",
                "stale": "BINARY DIFFERS FROM HEADER - inspect tools/out/decryptors.txt"}[it["direction"]]
        off = pe.rva2off(it["block_rva"])
        blob = pe.data[off:off + 64]
        h = 0x811C9DC5
        for byte in blob:
            h = ((h ^ byte) * 0x01000193) & 0xFFFFFFFF
        g.append(f"    // {it['name']}  GameAssembly+0x{it['func_rva']:X}  ({note})")
        g.append(f"    inline constexpr unsigned long long k{it['name']}Rva = 0x{it['func_rva']:X}ull;")
        g.append(f"    inline constexpr unsigned long long k{it['name']}BlockRva = 0x{it['block_rva']:X}ull;")
        g.append(f"    inline constexpr unsigned int k{it['name']}BlockHash = 0x{h:08X}u;")
        g.append(f"    inline unsigned int {it['name']}Word(unsigned int v)")
        g.append("    {")
        g.extend(emit_word([tuple(x) for x in it["decrypt_chain"]]))
        g.append("        return v;")
        g.append("    }")
        if it["wrapper"]:
            g.append(f"    inline unsigned long long {it['name']}(unsigned long long a1)")
            g.append("    {")
            g.append("        unsigned char flag = 0;")
            g.append("        unsigned long long raw = 0;")
            g.append("        if (!MemReadable(a1 + 0x10, 1)) return 0;")
            g.append("        SafeRead(a1 + 0x10, flag);")
            g.append("        if (!flag) return 0;")
            g.append("        SafeRead(a1 + 0x18, raw);")
            g.append(f"        unsigned int lo = {it['name']}Word((unsigned int)(raw & 0xFFFFFFFFu));")
            g.append(f"        unsigned int hi = {it['name']}Word((unsigned int)(raw >> 32));")
            g.append("        return ((unsigned long long)hi << 32) | lo;")
            g.append("    }")
        else:
            g.append(f"    inline unsigned long long {it['name']}(unsigned long long raw)")
            g.append("    {")
            g.append(f"        unsigned int lo = {it['name']}Word((unsigned int)(raw & 0xFFFFFFFFu));")
            g.append(f"        unsigned int hi = {it['name']}Word((unsigned int)(raw >> 32));")
            g.append("        return ((unsigned long long)hi << 32) | lo;")
            g.append("    }")
        g.append("")
    g.append("} // namespace generated")
    with open(os.path.join(GEN, "Decryptors.generated.h"), "w", encoding="utf-8") as f:
        f.write("\n".join(g) + "\n")
    print("[+] wrote", os.path.join(GEN, "Decryptors.generated.h"))
    print("[+] wrote", os.path.join(OUT, "decryptors.txt"))


if __name__ == "__main__":
    main()
