"""Look for a second Il2CppField copy whose offset is not EAC-poisoned.

EAC overwrites FieldInfo::offset with 0x67676767 in the runtime copy the
exported field_get_offset() returns.  The runtime itself does not need that
value (AOT code uses baked offsets), so the real number may still exist in a
parallel metadata copy.  This scans process memory for the field's name pointer
and prints the offset slot of every struct that references it.
"""
import struct
import sys

import pymem
import pymem.pattern


def main():
    pid = int(sys.argv[1]) if len(sys.argv) > 1 else 9040
    target_fields = [int(x, 16) for x in sys.argv[2:]] or [0x1C650DC27C0]
    pm = pymem.Pymem(pid)

    for faddr in target_fields:
        try:
            name_ptr = struct.unpack("<Q", pm.read_bytes(faddr, 8))[0]
        except Exception as e:
            print(f"[!] {faddr:#x}: {e}")
            continue
        print(f"\n=== field 0x{faddr:X} name_ptr=0x{name_ptr:X}")
        pat = struct.pack("<Q", name_ptr)
        try:
            hits = pymem.pattern.pattern_scan_all(pm.process_handle, pat, return_multiple=True)
        except TypeError:
            h = pymem.pattern.pattern_scan_all(pm.process_handle, pat)
            hits = [] if h in (None, 0) else [h]
        print(f"    name_ptr occurrences: {len(hits)}")
        for h in hits[:40]:
            try:
                off = struct.unpack("<I", pm.read_bytes(h + 0x18, 4))[0]
                parent = struct.unpack("<Q", pm.read_bytes(h + 0x10, 8))[0]
            except Exception:
                continue
            tag = ""
            if off == 0x67676767:
                tag = "  <-- POISON"
            elif 0 < off < 0x100000:
                tag = "  <-- PLAUSIBLE OFFSET"
            print(f"    struct 0x{h:X}  +0x10=0x{parent:X}  +0x18=0x{off:X}{tag}")


if __name__ == "__main__":
    main()
