"""
Locate every reference to the Instant Loot item-move routine (0x1834DB0)
inside GameAssembly.dll and list the enclosing .pdata function for each.

This tells us which classes bind it as a real method (so the class owning the
per-item move can be recovered without names, same trick as LootAllButton).

Usage: py -3 revers\find_item_move_refs.py
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rev_loot import Pe, DLL  # noqa: E402

TARGET = 0x1834DB0
TARGET_VA = 0x180000000 + TARGET  # image base of GameAssembly 26140533


def main():
    pe = Pe(DLL)
    funcs = pe.functions()
    starts = [f[0] for f in funcs]

    # 1) rel32 call/jmp references: e8/e9 + signed disp32 == target
    hits = []
    for sec in pe.sections:
        if not (sec["chars"] & 0x20000000):  # not executable
            continue
        off = sec["raw"]
        va = sec["va"]
        n = min(sec["rawsize"], sec["vsize"])
        blob = pe.data[off:off + n]
        for i in range(len(blob) - 5):
            if blob[i] in (0xE8, 0xE9):
                disp = struct.unpack_from("<i", blob, i + 1)[0]
                # va/i are RVAs here, so compare against the target RVA.
                if va + i + 5 + disp == TARGET:
                    hits.append(va + i)

    # 2) absolute pointer references to the code address (vtable / MethodInfo)
    ptrabs = struct.pack("<Q", TARGET_VA)
    ptr_hits = []
    for sec in pe.sections:
        off = sec["raw"]
        va = sec["va"]
        n = min(sec["rawsize"], sec["vsize"])
        blob = pe.data[off:off + n]
        start = 0
        while True:
            j = blob.find(ptrabs, start)
            if j < 0:
                break
            ptr_hits.append(va + j)
            start = j + 1

    def owner(x):
        import bisect
        k = bisect.bisect_right(starts, x) - 1
        if k >= 0:
            b, e = funcs[k]
            if b <= x < e:
                return "0x%X..0x%X" % (b, e)
        return "?"

    print("rel32 call/jmp refs to 0x%X:" % TARGET)
    for h in hits:
        print("  0x%08X  in fn %s" % (h, owner(h)))

    print("\nabsolute pointer refs to 0x%X (%d):" % (TARGET_VA, len(ptr_hits)))
    for h in ptr_hits[:80]:
        print("  0x%08X  in fn %s" % (h, owner(h)))

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "loot_item_move_refs.txt"), "w", encoding="utf-8") as f:
        f.write("target rva 0x%X va 0x%X\n\nrel32:\n" % (TARGET, TARGET_VA))
        for h in hits:
            f.write("  0x%08X  in fn %s\n" % (h, owner(h)))
        f.write("\nabsolute pointers:\n")
        for h in ptr_hits:
            f.write("  0x%08X  in fn %s\n" % (h, owner(h)))
    print("\nwrote out/loot_item_move_refs.txt")


if __name__ == "__main__":
    main()
