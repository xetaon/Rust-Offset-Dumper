"""Import named field offsets from the external 26140533 Generation.h.

``Vlone Rust Internal/Data/Generation.h`` was regenerated from the same build
(26140533) and its 106 field offsets were re-checked against a Rust-Offset-Dumper run,
so it is trustworthy (class, offset) evidence for names the UC thread does not
list.  Names are the author's identifiers (``player_model``), not metadata
names, so the generator keeps UC evidence on top of these.

Usage:
    py tools/import_generation.py [PATH-TO-Generation.h]
"""
from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "reference")
DEFAULT = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop",
                       "Vlone Rust Internal", "Data", "Generation.h")

RE_FIELD = re.compile(
    r"^\s*constexpr\s+uint32_t\s+(\w+)\s*=\s*(0x[0-9A-Fa-f]+)\s*;", re.M)
RE_CLASS = re.compile(r"^class\s+(\S+)\s*$")

# names that are decryptors / typeinfo / methods, never field offsets
SKIP_SUFFIX = ("_Decryptor", "_TypeInfo", "_Static")


def live_class_names(dump):
    names = set()
    if not os.path.exists(dump):
        return names
    for line in open(dump, encoding="utf-8", errors="ignore"):
        m = RE_CLASS.match(line.strip())
        if m:
            names.add(m.group(1))
    return names


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    if not os.path.exists(path):
        print(f"[!] not found: {path}")
        return 1
    dump = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop",
                        "Rust-Offset-DumperDumps", "Rust-Offset-Dumper_classes.txt")
    known = live_class_names(dump)

    rows = []
    text = open(path, encoding="utf-8", errors="ignore").read()
    # only the field-offset section, before the method/typeinfo blocks
    end = text.find("// ====", text.find("namespace fields"))
    body = text[:end] if end > 0 else text

    unknown = 0
    for m in RE_FIELD.finditer(body):
        ident, off = m.group(1), int(m.group(2), 16)
        if off == 0 or off > 0x100000:
            continue
        if ident.endswith(SKIP_SUFFIX):
            continue
        # longest live class name that prefixes the identifier
        cls = None
        for name in known:
            if ident.startswith(name + "_") and (cls is None or len(name) > len(cls)):
                cls = name
        if cls is None:
            unknown += 1
            continue
        field = ident[len(cls) + 1:]
        if not field or field in ("TypeInfo",):
            continue
        if field.endswith("Decryptor") or field.endswith("_TypeInfo"):
            continue
        rows.append((cls, off, field))

    os.makedirs(REF, exist_ok=True)
    out = os.path.join(REF, "generation_26140533.txt")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("# class+offset -> field name evidence (Generation.h, build 26140533)\n")
        f.write("# imported by tools/import_generation.py\n")
        for cls, off, name in sorted(set(rows)):
            f.write(f"{cls}+0x{off:X} = {name}\n")
    print(f"[+] {len(set(rows))} slot names -> {out}")
    if unknown:
        print(f"[!] {unknown} identifiers did not match a live class name")
    return 0


if __name__ == "__main__":
    sys.exit(main())
