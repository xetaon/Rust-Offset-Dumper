"""
Cross-check an external offsets header against the live dump.

Some offsets headers (e.g. the one posted on Discord for build 26140533) are
hand-curated.  This tool does not trust them either: it compares every
class/field/offset and every TypeInfo RVA with what the injected dumper
measured in the running process.

    py tools/check_reference.py path\\to\\reference_offsets.hpp
    py tools/check_reference.py ref.hpp --dumpdir %USERPROFILE%\\Desktop\\Rust-Offset-DumperDumps

Comparison rules:
  * class names are matched case-insensitively, namespace prefix ignored
  * a field is CONFIRMED when the live class has a field with the same name
    at the same offset
  * OFFSET-ONLY when the offset exists under another name (renamed field)
  * MISSING when the live class has no field at that offset
  * TypeInfo RVAs are confirmed only when the resolved dump marked them
    verified (slot -> klass -> name)
"""
from __future__ import annotations

import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import analyze_dump as A  # noqa: E402

RE_NS = re.compile(r"^\s*namespace\s+(\w+)\s*$")
RE_CONST = re.compile(r"^\s*(?:inline\s+)?(?:static\s+)?constexpr\s+[\w:<>]+\s+(\w+)\s*=\s*0x([0-9A-Fa-f]+)\s*;")
RE_CLOSE = re.compile(r"^\s*}\s*$")

META_NAMESPACES = {"GameAssembly", "il2cpp_api", "gc_handles", "klass_rvas",
                   "klass_layout", "decryption", "singleton_typeinfos"}


def parse_ref(path):
    """-> {namespace: {ident: value}} plus the raw namespace order."""
    out = {}
    stack = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            m = RE_NS.match(line)
            if m:
                stack.append(m.group(1))
                out.setdefault(m.group(1), {})
                continue
            m = RE_CONST.match(line)
            if m and stack:
                out.setdefault(stack[-1], {})[m.group(1)] = int(m.group(2), 16)
                continue
            if RE_CLOSE.match(line) and stack and "namespace" not in line:
                stack.pop()
    return out


def norm(n):
    return re.sub(r"[^a-z0-9]", "", n.lower())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reference")
    ap.add_argument("--dumpdir", default=A.DEFAULT_DUMP)
    args = ap.parse_args()

    off_path = os.path.join(args.dumpdir, "Rust-Offset-Dumper_offsets.h")
    res_path = os.path.join(args.dumpdir, "Rust-Offset-Dumper_resolved.h")
    if not os.path.exists(off_path):
        print(f"[!] no live dump: {off_path}")
        return 1

    live = A.parse_offsets(off_path)
    resolved = A.parse_resolved(res_path)
    ref = parse_ref(args.reference)

    # index live classes by normalized name
    live_by_name = {}
    for ident, c in live.items():
        live_by_name.setdefault(norm(c["name"]), []).append(c)

    total = confirmed = offset_only = missing = 0
    lines = []
    for ns, vals in ref.items():
        if ns in META_NAMESPACES:
            continue
        cls = live_by_name.get(norm(ns))
        if not cls:
            continue
        c = cls[0]
        by_name = {norm(f["name"]): f["offset"] for f in c["fields"]}
        by_off = {}
        for f in c["fields"]:
            by_off.setdefault(f["offset"], f["name"])
        for field, value in vals.items():
            total += 1
            lname = norm(field)
            if lname in by_name:
                if by_name[lname] == value:
                    confirmed += 1
                    tag = "CONFIRMED"
                else:
                    missing += 1
                    tag = f"MISMATCH ref=0x{value:X} live=0x{by_name[lname]:X}"
            elif value in by_off:
                offset_only += 1
                tag = f"OFFSET-ONLY live_name={by_off[value]}"
            else:
                missing += 1
                tag = "MISSING"
            lines.append(f"{ns:28s} {field:36s} 0x{value:04X}  {tag}")

    # TypeInfo RVAs from klass_rvas / *_TypeInfo namespaces
    ti_ref = {}
    for ns in ("klass_rvas",):
        for name, rva in ref.get(ns, {}).items():
            if name.endswith("_TypeInfo") or name in ("BaseNetworkable", "BasePlayer"):
                ti_ref[name.replace("_TypeInfo", "")] = rva
    ti_live = {n: v["typeinfo_rva"] for n, v in resolved["classes"].items()
               if v.get("typeinfo_verified")}
    ti_ok = ti_bad = 0
    for name, rva in ti_ref.items():
        match = next((k for k in ti_live if norm(k) == norm(name)), None)
        if match is not None and ti_live[match] == rva:
            ti_ok += 1
            lines.append(f"typeinfo                     {name:36s} 0x{rva:08X}  CONFIRMED")
        else:
            ti_bad += 1
            lines.append(f"typeinfo                     {name:36s} 0x{rva:08X}  UNVERIFIED")

    print("\n".join(lines))
    print(f"\n[+] fields: {total}  confirmed={confirmed}  offset-only={offset_only}  missing/mismatch={missing}")
    print(f"[+] typeinfo: {ti_ok} confirmed, {ti_bad} unverified")

    out = os.path.join(HERE, "out", "reference_check.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[+] wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
