#!/usr/bin/env python3
"""Import the verified field names from revers/out into the dumper.

`revers/rev_binary.py` proves every offset of BasePlayer / Projectile /
AttackEntity / PlayerModel against `GameAssembly.dll` alone and writes
`none revers/out/binary_provenance.json`.  The live dumper measures the same
slots through IL2CPP but cannot name the ones whose metadata name is a
40-hex EAC hash.

This script is the bridge: it reads the provenance (name, offset, type) and
emits `src/generated/ReversOffsets.generated.h`, which the DLL uses ONLY as a
name source.  The offset in the DLL always comes from the live process or from
the verified `.rdata` table - never from this header.

Usage:
    py -3 tools\\import_binary_offsets.py
    py -3 tools\\import_binary_offsets.py --provenance revers\\out\\binary_provenance.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GEN = os.path.join(ROOT, "src", "generated")
DEFAULT = os.path.join(ROOT, "revers", "out", "binary_provenance.json")


def sanitize(s: str) -> str:
    s = re.sub(r"[^0-9A-Za-z_]", "_", s)
    if not s or s[0].isdigit():
        s = "_" + s
    return s


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--provenance", default=DEFAULT)
    ap.add_argument("--out", default=os.path.join(GEN, "ReversOffsets.generated.h"))
    args = ap.parse_args()

    if not os.path.exists(args.provenance):
        print(f"[!] no provenance: {args.provenance}")
        print("    run: py -3 revers\\rev_binary.py")
        return 1

    with open(args.provenance, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = []
    for klass, fields in data.items():
        for f in fields:
            name = f.get("name") or ""
            if not name:
                continue
            rows.append({
                "klass": klass,
                "offset": int(f["offset"]),
                "name": name,
                "type": f.get("type") or "",
                "kind": f.get("kind") or "MISSING",
            })
    rows.sort(key=lambda r: (r["klass"], r["offset"], r["name"]))

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    L = []
    L.append("// ===========================================================================")
    L.append("//  ReversOffsets.generated.h - AUTO-GENERATED, DO NOT EDIT")
    L.append("//  source: revers/out/binary_provenance.json")
    L.append("//          (revers/rev_binary.py - static proof from GameAssembly.dll)")
    L.append("//")
    L.append("//  This table is a NAME SOURCE ONLY.  The dumper never takes an offset")
    L.append("//  from here: a slot is written only when the live runtime or the")
    L.append("//  verified .rdata offset table produced it.  The entry just supplies the")
    L.append("//  readable name for a slot whose metadata name is an EAC hash.")
    L.append("// ===========================================================================")
    L.append("#pragma once")
    L.append("#include <cstddef>")
    L.append("#include <cstdint>")
    L.append("#include <cstring>")
    L.append("")
    L.append("namespace revers_offsets")
    L.append("{")
    L.append("    struct Field")
    L.append("    {")
    L.append("        const char*    klass;")
    L.append("        std::uint32_t  offset;")
    L.append("        const char*    name;")
    L.append("        const char*    type;")
    L.append("        const char*    kind;   // table | code")
    L.append("    };")
    L.append("")
    L.append("    inline constexpr Field fields[] = {")
    for r in rows:
        L.append('        {{ "{k}", 0x{o:X}, "{n}", "{t}", "{kd}" }},'.format(
            k=r["klass"], o=r["offset"], n=r["name"],
            t=r["type"].replace('"', "'"), kd=r["kind"]))
    L.append("    };")
    L.append("    inline constexpr std::size_t field_count =")
    L.append("        sizeof(fields) / sizeof(fields[0]);")
    L.append("")
    L.append("    // exact (class, offset) lookup - the slot is already measured live")
    L.append("    inline const Field* Find(const char* klass, std::uint32_t offset)")
    L.append("    {")
    L.append("        if (!klass) return nullptr;")
    L.append("        for (const Field& f : fields)")
    L.append("            if (f.offset == offset && std::strcmp(f.klass, klass) == 0)")
    L.append("                return &f;")
    L.append("        return nullptr;")
    L.append("    }")
    L.append("")
    L.append("    inline const char* NameFor(const char* klass, std::uint32_t offset)")
    L.append("    {")
    L.append("        const Field* f = Find(klass, offset);")
    L.append("        return f ? f->name : nullptr;")
    L.append("    }")
    L.append("")
    L.append("    inline const char* TypeFor(const char* klass, std::uint32_t offset)")
    L.append("    {")
    L.append("        const Field* f = Find(klass, offset);")
    L.append("        return f ? f->type : nullptr;")
    L.append("    }")
    L.append("} // namespace revers_offsets")
    L.append("")

    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")

    per_class = {}
    for r in rows:
        per_class[r["klass"]] = per_class.get(r["klass"], 0) + 1
    for k in sorted(per_class):
        print(f"[+] {k:<14} {per_class[k]:>3} name(s)")
    print(f"[+] total {len(rows)} field names -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
