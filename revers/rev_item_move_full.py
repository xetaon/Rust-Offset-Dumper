"""
Deep disassembly of the Instant Loot per-item routine called by
LootAllButton::OnClicked (0x1834DB0) and its continuation chunks.

The .pdata table splits the routine into several contiguous COMDAT chunks
(0x1834DB0, 0x1834E29, 0x1835109, ...), so a plain "enclosing function"
lookup truncates it. This dumps the whole contiguous blob and follows
direct jumps / call targets that stay inside it.

Usage: py -3 revers/rev_item_move_full.py
"""
import os
import sys

import capstone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rev_loot import Pe, DLL  # noqa: E402

START = 0x1834DB0
END = 0x1835310  # past the last chunk start (0x1835150)


def main():
    pe = Pe(DLL)
    code = pe.read(START, END - START)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True
    lines = []
    targets = set()
    calls = set()
    for ins in md.disasm(code, START):
        lines.append("0x%08X  %-24s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
        if ins.mnemonic in ("call", "jmp", "je", "jne", "jz", "jnz", "ja", "jb", "jae", "jbe",
                            "jg", "jl", "jge", "jle", "js", "jns"):
            if ins.operands and ins.operands[0].type == capstone.x86.X86_OP_IMM:
                t = ins.operands[0].imm
                (calls if ins.mnemonic == "call" else targets).add(t)

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "loot_disasm_item_move_full.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("; Instant Loot per-item routine, contiguous blob 0x%X..0x%X\n" % (START, END))
        f.write("; called by LootAllButton::OnClicked at 0x463DD32 with rcx=item, dl=1\n\n")
        f.write("\n".join(lines) + "\n")
        f.write("\n; direct call targets: %s\n" % " ".join("0x%X" % c for c in sorted(calls)))
        f.write("; branches inside blob: %s\n" % " ".join(
            "0x%X" % t for t in sorted(targets) if START <= t < END))
        f.write("; branches outside blob: %s\n" % " ".join(
            "0x%X" % t for t in sorted(targets) if not (START <= t < END)))

    print("wrote", path, os.path.getsize(path), "bytes")
    print("calls:", " ".join("0x%X" % c for c in sorted(calls)))
    print("outside branches:", " ".join("0x%X" % t for t in sorted(targets)
                                        if not (START <= t < END)))


if __name__ == "__main__":
    main()
