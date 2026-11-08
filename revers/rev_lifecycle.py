"""
Disassemble the small lifecycle methods that reveal field offsets:
  LootAllButton::Awake      0x463DDD0  (2 declared fields)
  LootAllButton::.ctor      0x09CB140
  PlayerLoot::.ctor         0x35B1FF0  (4 declared fields, entitySource is #0)

Field offsets are NOT in metadata, but the ctor/Awake stores are.

Usage: py -3 revers\rev_lifecycle.py
"""
import os
import struct
import sys

import capstone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rev_loot import Pe, DLL  # noqa: E402

TARGETS = {
    "LootAllButton_Awake": 0x463DDD0,
    "LootAllButton_ctor": 0x09CB140,
    "PlayerLoot_ctor": 0x35B1FF0,
}


def fn_bounds(pe, rva):
    hit = [f for f in pe.functions() if f[0] <= rva < f[1]]
    return hit[0] if hit else (rva, rva + 0x300)


def main():
    pe = Pe(DLL)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
    os.makedirs(out, exist_ok=True)

    for name, rva in TARGETS.items():
        b, e = fn_bounds(pe, rva)
        code = pe.read(b, e - b)
        lines = ["; %s  0x%X..0x%X len 0x%X" % (name, b, e, e - b)]
        for ins in md.disasm(code, b):
            lines.append("0x%08X  %-24s %s %s" % (ins.address, ins.bytes.hex(),
                                                   ins.mnemonic, ins.op_str))
        path = os.path.join(out, "loot_disasm_%s.txt" % name)
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print("\n=== %s 0x%X..0x%X ===" % (name, b, e))
        # print only the interesting stores/loads first
        for line in lines:
            if any(t in line for t in ("+ 0x20]", "+ 0x28]", "+ 0x30]", "+ 0x38]",
                                       "+ 0x40]", "+ 0x48]", "0x463d", "0x35b1")):
                print(line)
        print("wrote", os.path.basename(path))


if __name__ == "__main__":
    main()
