"""
Find which PlayerLoot field offset is entitySource by scanning every
PlayerLoot method body for accesses to this+0x20 .. this+0x40.

Field order from metadata (revers/dump_fields.py):
  0 entitySource          <- plaintext name
  1 %6a6016... (object)
  2 %567871... (object)
  3 %87c173... (object)
and the class derives from a hashed base bigger than MonoBehaviour, so the
first declared field is expected at +0x28 (matches the live reference).

This script lists the candidate offsets, plus the methods that STORE to them
(the open/path setter) and the ones that LOAD and dereference them.

Usage: py -3 revers\rev_playerloot_fields.py
"""
import os
import sys

import capstone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rev_loot import Pe, DLL  # noqa: E402

PLAYERLOOT_METHODS = [
    0x035AEBD0, 0x035AEDD0, 0x035AF150, 0x008EA3D0, 0x035AF2C0, 0x035AF2D0,
    0x035AF440, 0x035AF8C0, 0x008EA3D0, 0x035AF910, 0x035AF920, 0x035AFAC0,
    0x035AFBD0, 0x035B0150, 0x035B06D0, 0x035B0860, 0x035B08B0, 0x035B0C30,
    0x035B0C90, 0x035B0CF0, 0x035B0EF0, 0x035B1080, 0x035B1190, 0x035B11F0,
    0x035B1360, 0x035B18E0, 0x035B1AE0, 0x008EA3D0, 0x035B1C70, 0x035B1FF0,
    0x035B2100, 0x035B22A0, 0x035B2710, 0x035B28A0, 0x035B2A30, 0x035B2FB0,
    0x035B2FC0, 0x035B3340, 0x035B33A0, 0x035B34B0, 0x035B3650, 0x035B37E0,
    0x035B3970, 0x035B39C0, 0x035B3AD0, 0x035B3BE0, 0x035B3D80, 0x035B3E90,
    0x035B4090, 0x035B4240, 0x035B4440, 0x035B4450, 0x035AF910, 0x035B45E0,
    0x035B47A0, 0x035B4800, 0x035B4970, 0x035B4A20, 0x035B4B00, 0x035B4D00,
    0x035B4E00, 0x035B4F00, 0x035B5100, 0x035B5200, 0x035B5300, 0x035B5400,
    0x035B5500, 0x035B5600, 0x035B5700, 0x035B5800, 0x035B5900, 0x035B5A00,
]


def bounds(pe, rva):
    hit = [f for f in pe.functions() if f[0] <= rva < f[1]]
    return hit[0] if hit else (rva, rva + 0x400)


def main():
    pe = Pe(DLL)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
    os.makedirs(out, exist_ok=True)
    lines = []
    stores = {}
    loads = {}
    seen = set()
    for rva in PLAYERLOOT_METHODS:
        if rva in seen or rva == 0x008EA3D0:
            continue
        seen.add(rva)
        b, e = bounds(pe, rva)
        if e - b > 0x4000:
            e = b + 0x4000
        code = pe.read(b, e - b)
        for ins in md.disasm(code, b):
            ops = ins.op_str
            if "] ," in ops or "]," in ops:
                pass
            # store: mov qword ptr [reg + 0xNN], reg2
            if ins.mnemonic.startswith("mov") and ", " in ops and ops.startswith(("qword ptr [", "dword ptr [", "byte ptr [")):
                pass
            for off in ("0x20", "0x28", "0x30", "0x38"):
                if "[%s + %s]" % ("r", off) in ops or ("+ %s]" % off) in ops:
                    pass
            # generic: find "+ 0x28]" style with a register base and report
            if any(("+ %s]" % o) in ops for o in ("0x20", "0x28", "0x30", "0x38")):
                is_store = ops.startswith(("qword ptr [", "dword ptr [", "byte ptr ["))
                line = "0x%08X  %-22s %s %s" % (ins.address, ins.bytes.hex(),
                                                 ins.mnemonic, ops)
                lines.append(line)
                if is_store:
                    for o in ("0x20", "0x28", "0x30", "0x38"):
                        if "+ %s]" % o in ops:
                            stores.setdefault(o, []).append(ins.address)
                else:
                    for o in ("0x20", "0x28", "0x30", "0x38"):
                        if "+ %s]" % o in ops:
                            loads.setdefault(o, []).append(ins.address)

    with open(os.path.join(out, "playerloot_field_access.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("field accesses found:", len(lines))
    for o in ("0x20", "0x28", "0x30", "0x38"):
        print("  +%s: stores=%d loads=%d" % (o, len(stores.get(o, [])), len(loads.get(o, []))))
        if stores.get(o):
            print("        store sites:", " ".join("0x%X" % x for x in stores[o][:12]))
    print("wrote out/playerloot_field_access.txt")


if __name__ == "__main__":
    main()
