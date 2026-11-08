"""Extract name evidence from the UnknownCheats build-26140533 thread page.

The page (saved as markdown by r.jina.ai) contains three independent dumps:

  1. a hand-checked JSON ``"Classes"`` object
  2. CLUSTDUMPER, a metadata-exact C++ SDK (``constexpr std::uintptr_t``)
  3. the Rust Runtime Dumper (``inline constexpr size_t`` + ``// Hash: %..``)

All three are reduced to two evidence files that gen_overrides.py consumes:

    tools/reference/names_extra.txt       Class+0xOFF = name   @ type
    tools/reference/hash_names_extra.txt  %hash = name

Only offsets are imported here - nothing is applied to the live dump unless
the same (class, offset) exists there.  Source priority is JSON > CLUSTDUMPER >
Runtime Dumper; the type annotation is kept so the generator can reject an
override that lands on a different field type (duplicate class names).
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "reference")
DEFAULT_PAGE = os.path.join(os.environ.get("TEMP", ""), "uc1365.md")

RE_JSON_VALUE = re.compile(r'^\s*"([^"]+)"\s*:\s*"(0x[0-9A-Fa-f]+)"\s*,?\s*$')
RE_SDK_FIELD = re.compile(
    r"constexpr\s+std::uintptr_t\s+(\w+)\s*=\s*(0x[0-9A-Fa-f]+)\s*;"
    r"\s*//\s*(live|meta|code|engine)(?:\s+(\S+))?")
RE_RT_FIELD = re.compile(r"inline constexpr size_t\s+(\w+)\s*=\s*(0x[0-9A-Fa-f]+)\s*;")
RE_NS = re.compile(r"(?://\s*Hash:\s*%([0-9a-fA-F]{40})\s*\n)?namespace\s+(\w+)\s*\{")
RE_CLASS_HASH = re.compile(r"//\s*Hash:\s*%([0-9a-fA-F]{40})\s*\nnamespace\s+(\w+)")


def block_after(text, start):
    """Return the body of the {...} block whose opening brace is at start."""
    depth = 1
    k = start
    while k < len(text) and depth:
        if text[k] == "{":
            depth += 1
        elif text[k] == "}":
            depth -= 1
        k += 1
    return text[start:k - 1]


def json_classes(text):
    i = text.index('"Classes":')
    j = text.index("{", i)
    raw = text[j:j + len(block_after(text, j + 1)) + 2]
    clean = raw.replace("\xa0", "").replace("\ufffd", "")
    # the paste is missing a few commas between string members
    clean = re.sub(r'("(?:0x[0-9A-Fa-f]+|[^"\n]*)")\s*\n(\s*")', r"\1,\n\2", clean)
    clean = re.sub(r",(\s*[}\]])", r"\1", clean)
    data = json.loads(clean)
    out = []
    for cls, fields in data.items():
        if not isinstance(fields, dict):
            continue
        for name, off in fields.items():
            if isinstance(off, dict):          # nested struct -> Class.field
                for sub, suboff in off.items():
                    out.append((cls, int(suboff, 16), sub, ""))
            elif isinstance(off, str) and off.startswith("0x"):
                out.append((cls, int(off, 16), name, ""))
    return out


def namespaces(text, limit=0x100000):
    """[(namespace, hash, [(offset, name, type, kind)])] for every C++ block."""
    out = []
    for m in RE_NS.finditer(text):
        ns = m.group(2)
        body = block_after(text, m.end())
        fields = []
        for fm in RE_SDK_FIELD.finditer(body):
            off = int(fm.group(2), 16)
            if 0 < off <= limit:
                fields.append((off, fm.group(1), fm.group(4) or "", fm.group(3)))
        for fm in RE_RT_FIELD.finditer(body):
            off = int(fm.group(2), 16)
            if 0 < off <= limit:
                fields.append((off, fm.group(1), "", "rt"))
        if fields:
            out.append((ns, m.group(1), fields))
    return out


def main():
    page = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PAGE
    if not os.path.exists(page):
        print(f"[!] page not found: {page}")
        return 1
    text = open(page, encoding="utf-8", errors="ignore").read()

    names = {}          # (class, offset) -> (name, type)
    priority = {}       # (class, offset) -> source rank (lower wins)
    class_hashes = {}

    for cls, off, name, typ in json_classes(text):
        if off == 0 or not name:
            continue
        names[(cls, off)] = (name, typ)
        priority[(cls, off)] = 0

    # CLUSTDUMPER block only: the page has older dumps with different formats
    sdk_start = text.find("CLUSTDUMPER - Rust client SDK")
    sdk_text = text[sdk_start:] if sdk_start >= 0 else ""
    for ns, h, fields in namespaces(sdk_text):
        for off, name, typ, kind in fields:
            key = (ns, off)
            if priority.get(key, 99) <= 1:
                continue
            names[key] = (name, typ)
            priority[key] = 1

    rt_start = text.find("Rust Runtime Dumper")
    rt_text = text[rt_start:] if rt_start >= 0 else ""
    for ns, h, fields in namespaces(rt_text):
        for off, name, typ, kind in fields:
            key = (ns, off)
            if priority.get(key, 99) <= 2:
                continue
            names[key] = (name, typ)
            priority[key] = 2

    for m in RE_CLASS_HASH.finditer(text):
        class_hashes.setdefault(m.group(1).lower(), m.group(2))

    os.makedirs(REF, exist_ok=True)
    np = os.path.join(REF, "names_extra.txt")
    with open(np, "w", encoding="utf-8", newline="\n") as f:
        f.write("# class+offset -> field name evidence\n")
        f.write("# extracted from the build-26140533 UC thread by import_uc1365.py\n")
        f.write("# format: Class+0xOFF = name    @ FieldType (type is optional)\n")
        for (cls, off), (name, typ) in sorted(names.items()):
            tail = f"    @ {typ}" if typ else ""
            f.write(f"{cls}+0x{off:X} = {name}{tail}\n")

    hp = os.path.join(REF, "hash_names_extra.txt")
    with open(hp, "w", encoding="utf-8", newline="\n") as f:
        f.write("# %hash = class name evidence\n")
        for h, name in sorted(class_hashes.items()):
            f.write(f"%{h} = {name}\n")

    print(f"[+] {len(names)} slot names -> {np}")
    print(f"[+] {len(class_hashes)} class hashes -> {hp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
