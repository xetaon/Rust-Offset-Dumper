"""Generate name overrides for EAC-hashed identifiers.

The 40-hex tokens in the live dump are a *keyed* one-way hash: they cannot be
reversed.  Names can therefore only come from evidence - a source that saw the
same (class, offset) slot under a readable name.

Sources, in order of trust:

  1. tools/reference/names_extra.txt        (UC thread: JSON + CLUSTDUMPER + RT)
  2. tools/reference/cheatoffsets_*.txt     (community offsets, class+offset)
  3. tools/reference/hash_names_extra.txt   (hash -> name)
  4. the live dump itself                   (which slots are hashed where)

The live dump contains several *different* classes that share a name (``Item``
appears 9 times).  Evidence is therefore never applied by name alone: for a
duplicated name the variant whose field offsets (and types) match the evidence
is chosen, and every emitted override carries the expected field type so the
dumper can reject a slot that landed on a different field.

Usage:
    py tools/gen_overrides.py [--dump PATH] [--strict]
"""
from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import reference_parse as R  # noqa: E402

GEN = os.path.join(ROOT, "src", "generated")
REF = os.path.join(HERE, "reference")
DEFAULT_DUMP = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop",
                            "Rust-Offset-DumperDumps", "Rust-Offset-Dumper_classes.txt")

RE_CLASS = re.compile(r"^class\s+(\S+)\s*$")
RE_FIELD = re.compile(
    r"^\s*\+0x([0-9A-Fa-f]+)\s+(\S+)\s+(\S+)\s*:\s*(.*?)\s*(?:\[%([0-9a-fA-F]{40})\])?\s*$")


def norm(x):
    return re.sub(r"[^a-z0-9]", "", x.lower())


def type_matches(expected, actual):
    """Loose C#/SDK type comparison (float <-> System.Single, string <-> System.String)."""
    if not expected or not actual:
        return True
    if actual.startswith("%"):
        # the live type name is itself hashed - nothing to compare against
        return True
    if actual.strip().lower() in ("system.object", "object"):
        # metadata declares the base type; the SDK names the concrete one
        return True
    table = {
        "float": "single", "single": "single",
        "int": "int32", "int32": "int32", "uint": "uint32", "uint32": "uint32",
        "long": "int64", "int64": "int64", "ulong": "uint64", "uint64": "uint64",
        "short": "int16", "int16": "int16", "ushort": "uint16", "uint16": "uint16",
        "byte": "byte", "sbyte": "sbyte", "bool": "boolean", "boolean": "boolean",
        "string": "string", "object": "object", "double": "double",
    }

    def canon(t):
        t = t.strip().lower().split(".")[-1]
        t = t.replace("[]", "array")
        return table.get(t, t)

    return canon(expected) == canon(actual) or canon(expected) in canon(actual) \
        or canon(actual) in canon(expected)


def load_live(path):
    """Every class block in the live dump, with types and raw hashes."""
    out = []
    cur = None
    for line in open(path, "r", encoding="utf-8", errors="ignore"):
        m = RE_CLASS.match(line.strip())
        if m:
            cur = {"name": m.group(1), "klass": "", "fields": []}
            out.append(cur)
            continue
        if cur is None:
            continue
        m = re.match(r"\s*klass=(\S+)\s+parent=(\S+)", line)
        if m:
            cur["klass"] = m.group(1)
            continue
        if "[%" not in line:
            continue
        m = RE_FIELD.match(line)
        if not m:
            continue
        cur["fields"].append({
            "off": int(m.group(1), 16),
            "flags": m.group(2),
            "type": m.group(4).strip(),
            "hash": (m.group(5) or "").lower(),
        })
    return out


def read_pair_file(path, hash_first=False):
    """`Class+0xOFF = Name [@ Type]` or `<hash> = Name`, one per line."""
    out = []
    if not os.path.exists(path):
        return out
    for line in open(path, "r", encoding="utf-8", errors="ignore"):
        line = line.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        left, right = line.split("=", 1)
        typ = ""
        if "@" in right:
            right, typ = right.split("@", 1)
            typ = typ.strip()
        name = right.strip()
        if not name:
            continue
        left = left.strip()
        m = re.match(r"^(\S+?)\s*\+\s*0x([0-9A-Fa-f]+)$", left)
        if m and not hash_first:
            out.append((m.group(1), int(m.group(2), 16), name, typ))
            continue
        h = left.lstrip("%_").lower()
        if re.fullmatch(r"[0-9a-f]{40}", h):
            out.append((h, name))
    return out


def build_evidence():
    """(class, offset) -> (name, expectedType, priority).  Lower priority wins."""
    ev = {}

    def put(cls, off, name, typ, prio):
        key = (cls, off)
        cur = ev.get(key)
        if cur is None or prio < cur[2]:
            ev[key] = (name, typ, prio)

    for cls, off, name, typ in read_pair_file(os.path.join(REF, "names_extra.txt")):
        put(cls, off, name, typ, 0)

    # Generation.h: same build, field offsets re-checked against Rust-Offset-Dumper
    for cls, off, name, typ in read_pair_file(os.path.join(REF, "generation_26140533.txt")):
        put(cls, off, name, typ, 2)

    ref = R.load()
    for cls, vals in ref["fields"].items():
        for off, name in vals.items():
            put(cls, off, name, "", 3)
    return ev


def evidence_class(ev, name):
    """Evidence rows for a class name, tolerating namespace prefixes."""
    rows = {off: (n, t) for (cls, off), (n, t, _p) in ev.items() if cls == name}
    if rows:
        return rows
    k = norm(name)
    for (cls, off), (n, t, _p) in ev.items():
        if norm(cls) == k:
            rows[off] = (n, t)
    return rows


def main():
    args = sys.argv[1:]
    dump = DEFAULT_DUMP
    if "--dump" in args:
        dump = args[args.index("--dump") + 1]

    if not os.path.exists(dump):
        print(f"[!] no live dump: {dump}")
        print("    run the DLL once (F8) and re-run this script")
        return 1

    classes = load_live(dump)
    hashed = [(c["name"], f["off"], f["hash"], f["type"])
              for c in classes for f in c["fields"] if f["hash"]]
    print(f"[+] live hashed field slots: {len(hashed)}  ({len(classes)} classes)")

    ev = build_evidence()

    # group live class variants by name, pick the one the evidence describes
    by_name = {}
    for c in classes:
        by_name.setdefault(c["name"], []).append(c)

    selected = []
    ambiguous = []
    for name, variants in by_name.items():
        rows = evidence_class(ev, name)
        if not rows:
            continue
        if len(variants) == 1:
            selected.append((variants[0], rows))
            continue
        scored = []
        for v in variants:
            score = 0
            for f in v["fields"]:
                hit = rows.get(f["off"])
                if not hit:
                    continue
                score += 1
                if hit[1] and type_matches(hit[1], f["type"]):
                    score += 2
            scored.append((score, v))
        scored.sort(key=lambda x: -x[0])
        if scored[0][0] > 0:
            selected.append((scored[0][1], rows))
            if len(scored) > 1 and scored[1][0] == scored[0][0]:
                ambiguous.append(name)

    # slot + hash evidence from the chosen variants
    slot_names = {}
    hash_names = {}
    hash_prio = {}
    hash_src = {}
    for v, rows in selected:
        for f in v["fields"]:
            if not f["hash"]:
                continue
            hit = rows.get(f["off"])
            if not hit:
                continue
            name, etype = hit
            if etype and not type_matches(etype, f["type"]):
                continue
            slot_names[(v["name"], f["off"])] = name
            old = hash_prio.get(f["hash"], 99)
            if 0 <= old:
                if hash_names.get(f["hash"]) not in (None, name):
                    print(f"[!] hash {f['hash']} claimed by "
                          f"'{hash_names[f['hash']]}' and '{name}' - keeping first")
                if old <= 0:
                    continue
            hash_names[f["hash"]] = name
            hash_prio[f["hash"]] = 0
            hash_src[f["hash"]] = v["name"]

    # explicit hash evidence wins over slot-derived evidence
    for h, name in read_pair_file(os.path.join(REF, "hash_names_extra.txt"), hash_first=True):
        hash_names[h] = name

    field_map = []
    missing = []
    for cls, off, h, ftype in hashed:
        name = slot_names.get((cls, off))
        if not name or h not in hash_names:
            name = hash_names.get(h)
        if name:
            field_map.append((cls, off, h, name, ftype))
        else:
            missing.append((cls, off, h, ftype))

    class_map = dict(R.load()["hashed_classes"])
    for h, name in read_pair_file(os.path.join(REF, "hash_names_extra.txt"), hash_first=True):
        class_map[h] = name

    os.makedirs(GEN, exist_ok=True)
    p = os.path.join(GEN, "NameOverrides.generated.h")
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write("// AUTO-GENERATED by tools/gen_overrides.py - DO NOT EDIT\n")
        f.write("// source: live dump + UC 26140533 thread + tools/reference/*.txt\n")
        f.write("#pragma once\n#include <cstdint>\n\n")
        f.write("namespace name_overrides\n{\n")
        f.write("    // expected_type guards against duplicate class names: an entry\n")
        f.write("    // only fires when the live slot has a compatible field type.\n")
        f.write("    struct FieldName { const char* klass; std::uint32_t offset;"
                " const char* name; const char* expected_type; };\n")
        f.write("    inline constexpr FieldName fields[] = {\n")
        seen = set()
        for cls, off, h, name, ftype in sorted(field_map):
            if (cls, off) in seen:
                continue
            seen.add((cls, off))
            f.write(f'        {{ "{cls}", 0x{off:X}, "{name}", "{ftype}" }}, // %{h}\n')
        f.write("    };\n\n")
        f.write("    // hash -> name for every identifier we can name (classes + fields).\n")
        f.write("    // One entry applies everywhere the hash is used (class, field, type).\n")
        f.write("    struct HashName { const char* hash; const char* name; };\n")
        f.write("    inline constexpr HashName hashes[] = {\n")
        for h, name in sorted(hash_names.items()):
            f.write(f'        {{ "{h}", "{name}" }},\n')
        f.write("    };\n\n")
        f.write("    struct KlassName { const char* hash; const char* name; };\n")
        f.write("    inline constexpr KlassName classes[] = {\n")
        for h, name in sorted(class_map.items()):
            f.write(f'        {{ "{h}", "{name}" }},\n')
        f.write("    };\n")
        f.write("} // namespace name_overrides\n")
    print(f"[+] wrote {p}")
    print(f"[+] slot names: {len(seen)} / {len(hashed)} hashed field slots"
          f"   hash names: {len(hash_names)}   class names: {len(class_map)}")
    print(f"[!] still unnamed: {len(missing)}")
    if ambiguous:
        print("[!] ambiguous class variants (same score): " + ", ".join(sorted(ambiguous)))

    by_class = {}
    for cls, off, h, ftype in missing:
        by_class.setdefault(cls, []).append((off, h, ftype))
    for cls in sorted(by_class):
        print(f"    {cls}: {len(by_class[cls])} unnamed")
    if missing:
        print("\n[>] paste evidence into tools/reference/names_extra.txt:")
        print("    Class+0xOFFSET = realName    # then re-run this generator")
    return 0


if __name__ == "__main__":
    sys.exit(main())
