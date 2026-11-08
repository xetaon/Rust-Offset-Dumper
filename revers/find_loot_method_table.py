"""
Find the .data method-pointer table that contains LootAllButton::OnClicked
(0x463DB40) and dump its neighbours.

il2cpp emits MethodInfo objects whose first qword is methodPointer, and for
Unity UI components it also keeps a flat method-pointer table. Locating
OnClicked's slot lets us disassemble the class's other methods (Awake etc.)
without needing metadata names - which is exactly what Instant Loot needs on
this build.

Usage: py -3 revers\find_loot_method_table.py
"""
import os
import struct
import sys

import capstone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rev_loot import Pe, DLL  # noqa: E402

IMAGE_BASE = 0x180000000
ONCLICKED = 0x463DB40
WINDOW = 40  # qwords shown around the hit


def main():
    pe = Pe(DLL)
    needle = struct.pack("<Q", IMAGE_BASE + ONCLICKED)
    hits = []
    for sec in pe.sections:
        off, va = sec["raw"], sec["va"]
        n = min(sec["rawsize"], sec["vsize"])
        blob = pe.data[off:off + n]
        start = 0
        while True:
            j = blob.find(needle, start)
            if j < 0:
                break
            hits.append(va + j)
            start = j + 1

    print("absolute pointers to OnClicked 0x%X: %d" % (IMAGE_BASE + ONCLICKED, len(hits)))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
    os.makedirs(out, exist_ok=True)
    lines = []
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

    for h in hits:
        print("  slot 0x%X" % h)
        lines.append("=== slot 0x%X ===" % h)
        base = h - WINDOW * 8
        for i in range(WINDOW * 2 + 1):
            a = base + i * 8
            v = struct.unpack("<Q", pe.read(a, 8))[0]
            tag = ""
            if h <= a < h + 8:
                tag = "   <== OnClicked slot"
            elif 0x180000000 <= v < 0x180000000 + pe.size_of_image:
                tag = "   rva 0x%X" % (v - IMAGE_BASE)
            lines.append("  0x%08X  %016X%s" % (a, v, tag))
        lines.append("")
    with open(os.path.join(out, "loot_method_table.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("wrote out/loot_method_table.txt")

    # For each concrete function pointer near the hit, disassemble the first
    # few instructions so Awake (a short Unity message) is easy to spot.
    for h in hits:
        base = h - WINDOW * 8
        print("\n--- candidates around 0x%X ---" % h)
        for i in range(WINDOW * 2 + 1):
            a = base + i * 8
            v = struct.unpack("<Q", pe.read(a, 8))[0]
            rva = v - IMAGE_BASE
            if rva <= 0 or rva >= pe.size_of_image:
                continue
            code = pe.read(rva, 24)
            ins = list(md.disasm(code, rva))[:4]
            if not ins:
                continue
            print("  slot 0x%08X rva 0x%08X  %s" % (
                a, rva, " ; ".join("%s %s" % (x.mnemonic, x.op_str) for x in ins)))


if __name__ == "__main__":
    main()
