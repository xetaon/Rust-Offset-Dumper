"""
Dump il2cpp field definitions (name / order / token) for a type, using the
existing v39 reader in tools/meta_rva.py.

Field *offsets* are not stored in metadata - they are computed at runtime -
but the declared order plus disassembly of the type's Awake/ctor is enough to
tie a name to the live offsets already seen in the log (LootAllButton+0x28,
PlayerLoot+0x28, PlayerInventory+0x48, ...).

Usage: py -3 revers\dump_fields.py LootAllButton PlayerLoot PlayerInventory
"""
import os
import struct
import sys

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools")
sys.path.insert(0, TOOLS)
from meta_rva import Metadata, DEFAULT_METADATA  # noqa: E402


def dump(meta, name):
    hits = [meta.type(i) for i in range(meta.type_count)
            if (meta.type(i)["name"] or "") == name]
    if not hits:
        print("type %r not found" % name)
        return
    for t in hits:
        ns = (t["namespace"] + ".") if t["namespace"] else ""
        print("TYPE %d %s%s token=%#010x fields=%d firstField=%d"
              % (t["index"], ns, t["name"], t["token"], t["field_count"], t["first_field"]))
        off = meta.sections["fields"][0]
        for k in range(t["field_count"]):
            b = off + (t["first_field"] + k) * 12
            name_idx, type_idx, token = struct.unpack_from("<iiI", meta.data, b)
            print("  ord=%2d  name=%-28s type_idx=%-6d token=%#010x"
                  % (k, meta.string(name_idx), type_idx, token))
        print()


def main():
    meta = Metadata(DEFAULT_METADATA)
    names = sys.argv[1:] or ["LootAllButton"]
    for n in names:
        dump(meta, n)


if __name__ == "__main__":
    main()
