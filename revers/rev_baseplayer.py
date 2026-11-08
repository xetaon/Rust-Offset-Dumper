#!/usr/bin/env python3
"""
rev_baseplayer.py - resolve the BasePlayer field layout for build 26140533.

Field *offsets* are not stored in global-metadata.dat (the il2cpp runtime
computes them from the declared layout).  This script therefore does not
invent offsets: it joins evidence that already exists for the exact same build
and prints the provenance of every number.

Sources (lowest priority wins):

  0. src/generated/Offsets.generated.h  - previous LIVE dump of this build
  1. tools/reference/names_extra.txt     - UC thread: class+offset -> name
  2. tools/reference/generation_*.txt    - Generation.h, live-checked
  3. tools/reference/cheatoffsets_*.txt  - community offsets
  4. src/generated/NameOverrides.generated.h - %hash -> name (+ slot hash)

The declared field order and the 40-hex hashes come from live metadata
(tools/meta_rva.py).  A metadata field is only bound to an offset when:

  * the evidence names that exact hash (NameOverrides comment), or
  * the hash resolves to a name that the evidence places at exactly one
    offset, or
  * the field is plaintext and the evidence places that name once.

Everything else is reported as UNRESOLVED instead of guessed.

Outputs (revers/out/):
  BasePlayer_offsets.h    requested fields + decryptor RVAs
  baseplayer_fields.json  full join result with provenance
  baseplayer_report.md    human-readable report

Usage:
    py -3 revers\\rev_baseplayer.py
    py -3 revers\\rev_baseplayer.py --all
"""
from __future__ import annotations

import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOOLS = os.path.join(ROOT, "tools")
OUT = os.path.join(HERE, "out")
sys.path.insert(0, TOOLS)

from meta_rva import Metadata, DEFAULT_METADATA  # noqa: E402
import reference_parse as R  # noqa: E402

GEN = os.path.join(ROOT, "src", "generated")
NAME_OVERRIDES = os.path.join(GEN, "NameOverrides.generated.h")
OFFSETS_GENERATED = os.path.join(GEN, "Offsets.generated.h")
DECRYPTORS = os.path.join(GEN, "Decryptors.generated.h")
REF = os.path.join(TOOLS, "reference")

RE_HASH = re.compile(r"^%([0-9a-fA-F]{40})$")


# --------------------------------------------------------------------------
# evidence loaders
# --------------------------------------------------------------------------
def read_pair_file(path, hash_first=False):
    """`Class+0xOFF = Name [@ Type]` or `<hash> = Name`."""
    out = []
    if not os.path.exists(path):
        return out
    for line in open(path, encoding="utf-8", errors="ignore"):
        line = line.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        left, right = line.split("=", 1)
        typ = ""
        if "@" in right:
            right, typ = right.split("@", 1)
            typ = typ.strip().rstrip(",").strip()
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
    return out  # type: ignore[return-value]


def load_name_overrides(path):
    fields = []   # (klass, offset, name, type, hash)
    hashes = {}   # hash -> name
    if not os.path.exists(path):
        return fields, hashes
    text = open(path, encoding="utf-8", errors="ignore").read()

    re_field = re.compile(
        r'\{\s*"([^"]+)"\s*,\s*0x([0-9A-Fa-f]+)\s*,\s*"([^"]*)"\s*,'
        r'\s*"([^"]*)"\s*\}\s*,?\s*(?://\s*%([0-9a-fA-F]{40}))?')
    for m in re_field.finditer(text):
        fields.append((m.group(1), int(m.group(2), 16), m.group(3),
                       m.group(4), (m.group(5) or "").lower()))

    re_hash = re.compile(r'\{\s*"([0-9a-fA-F]{40})"\s*,\s*"([^"]+)"\s*\}')
    for m in re_hash.finditer(text):
        hashes[m.group(1).lower()] = m.group(2)
    return fields, hashes


def load_offsets_generated_all(path):
    """{namespace: {field: offset}} from a previous live dump header."""
    out = {}
    if not os.path.exists(path):
        return out
    text = open(path, encoding="utf-8", errors="ignore").read()
    for m in re.finditer(r"namespace\s+(\w+)\s*\{(.*?)\n\s*\}", text, re.S):
        rows = {}
        for f in re.finditer(
                r"inline\s+constexpr\s+std::size_t\s+(\w+)\s*=\s*0x([0-9A-Fa-f]+)",
                m.group(2)):
            rows[f.group(1)] = int(f.group(2), 16)
        if rows:
            out[m.group(1)] = rows
    return out


def load_offsets_generated(path, klass="BasePlayer"):
    """Fields of one class from a previous live dump header."""
    return load_offsets_generated_all(path).get(klass, {})


class Evidence:
    """(class, offset) -> (name, type, priority) plus every observed alias."""

    def __init__(self):
        self.rows = {}
        self.aliases = {}   # norm(name) -> set(offset), per class

    def put(self, cls, off, name, typ, prio):
        key = (cls, off)
        cur = self.rows.get(key)
        if cur is None or prio < cur[2]:
            self.rows[key] = (name, typ, prio)
        # a slot can legitimately carry different names in different sources
        # (BasePlayer+0x2F0 = userIDString / _displayName) - keep both, never
        # silently drop the losing alias.
        self.aliases.setdefault(cls, {}).setdefault(norm(name), set()).add(off)


def build_evidence():
    ev = Evidence()

    for klass, fields in load_offsets_generated_all(OFFSETS_GENERATED).items():
        for name, off in fields.items():
            ev.put(klass, off, name, "", 0)
    for cls, off, name, typ in read_pair_file(os.path.join(REF, "names_extra.txt")):
        ev.put(cls, off, name, typ, 1)
    for cls, off, name, typ in read_pair_file(os.path.join(REF, "generation_26140533.txt")):
        ev.put(cls, off, name, typ, 2)
    ref = R.load()
    for cls, vals in ref["fields"].items():
        for off, name in vals.items():
            ev.put(cls, off, name, "", 3)
    for cls, off, name, typ, _h in load_name_overrides(NAME_OVERRIDES)[0]:
        ev.put(cls, off, name, typ, 4)
    return ev


def norm(x):
    return re.sub(r"[^a-z0-9]", "", x.lower())


def evidence_for_class(ev, klass):
    rows = {off: (n, t, p) for (c, off), (n, t, p) in ev.rows.items() if c == klass}
    if rows:
        return rows
    k = norm(klass)
    for (c, off), (n, t, p) in ev.rows.items():
        if norm(c) == k:
            rows[off] = (n, t, p)
    return rows


def aliases_for_class(ev, klass):
    """norm(name) -> set(offset) for one class, merging namespace variants."""
    direct = ev.aliases.get(klass, {})
    out = {}
    for n, offs in direct.items():
        out.setdefault(n, set()).update(offs)
    if direct:
        return out
    k = norm(klass)
    for c, table in ev.aliases.items():
        if norm(c) != k:
            continue
        for n, offs in table.items():
            out.setdefault(n, set()).update(offs)
    return out


def decryptor_map():
    out = {}
    if not os.path.exists(DECRYPTORS):
        return out
    text = open(DECRYPTORS, encoding="utf-8", errors="ignore").read()
    for m in re.finditer(
            r'inline\s+constexpr\s+unsigned\s+long\s+long\s+k(\w+?)Rva\s*=\s*0x([0-9A-Fa-f]+)',
            text):
        out[m.group(1)] = int(m.group(2), 16)
    return out


# --------------------------------------------------------------------------
# metadata join
# --------------------------------------------------------------------------
def type_name(meta, type_index, hashes):
    td = meta.sections["typeDefinitions"]
    if type_index < 0 or type_index >= td[2]:
        return f"il2cpp_type:{type_index}"
    t = meta.type(type_index)
    nm = t["name"] or ""
    if nm.startswith("%"):
        nm = hashes.get(nm[1:].lower(), nm)
    ns = t["namespace"] or ""
    if ns.startswith("%"):
        ns = hashes.get(ns[1:].lower(), ns)
    return f"{ns}.{nm}" if ns else nm


def baseplayer_fields(meta, hashes):
    hits = [meta.type(i) for i in range(meta.type_count)
            if (meta.type(i)["name"] or "") == "BasePlayer"]
    if not hits:
        raise SystemExit("BasePlayer type not found in metadata")
    t = hits[0]
    off = meta.sections["fields"][0]
    rows = []
    for k in range(t["field_count"]):
        b = off + (t["first_field"] + k) * 12
        name_idx, type_idx, token = struct.unpack_from("<iiI", meta.data, b)
        raw = meta.string(name_idx) or ""
        m = RE_HASH.match(raw)
        rows.append({
            "order": k,
            "raw": raw,
            "hash": m.group(1).lower() if m else "",
            "type": type_name(meta, type_idx, hashes),
            "token": token,
        })
    return t, rows


# --------------------------------------------------------------------------
# canonical request table: canonical name -> accepted metadata/evidence aliases
# --------------------------------------------------------------------------
REQUESTED = [
    ("UserIDString",            ["userIDString", "UserIDString"]),
    ("blueprints",              ["blueprints"]),
    ("lastSentTick",            ["lastSentTick"]),
    ("currentTeam",             ["currentTeam", "current_team"]),
    ("modelState",              ["modelState"]),
    ("voiceRecorder",           ["voiceRecorder"]),
    ("eyes",                    ["eyes", "playerEyes"]),
    ("GestureViewModel",        ["GestureViewModel"]),
    ("input",                   ["input"]),
    ("metabolism",              ["metabolism"]),
    ("hidden_CapsuleCollider",  ["hidden_CapsuleCollider"]),
    ("playerRigidbody",         ["playerRigidbody"]),
    ("movement",                ["movement"]),
    ("clActiveItem",            ["clActiveItem"]),
    ("inventory",               ["inventory"]),
    ("mounted",                 ["mounted"]),
    ("fallDamageEffect",        ["fallDamageEffect"]),
    ("drownEffect",             ["drownEffect"]),
    ("playerFlags",             ["playerFlags"]),
    ("_displayName",            ["_displayName", "display_name"]),
    ("voiceSpeaker",            ["voiceSpeaker"]),
    ("modifiers",               ["modifiers"]),
    ("userID",                  ["userID"]),
    ("playerModel",             ["playerModel"]),
]

DECRYPT_FOR = {
    "eyes": "PlayerEyesDecrypt",
    "hidden_CapsuleCollider": "BasePlayerCapsuleCollider",
    "clActiveItem": "ClActiveItemDecrypt",
    "inventory": "PlayerInventoryDecrypt",
    "userID": "UserIDDecrypt",
}


def main():
    argv = sys.argv[1:]
    dump_all = "--all" in argv

    meta = Metadata(DEFAULT_METADATA)
    ov_fields, ov_hashes = load_name_overrides(NAME_OVERRIDES)
    for h, name in read_pair_file(os.path.join(REF, "hash_names_extra.txt"),
                                  hash_first=True):
        ov_hashes.setdefault(h, name)

    # hash -> offset is authoritative when the header names that exact hash
    hash_offset = {}
    for cls, off, _name, _typ, h in ov_fields:
        if cls == "BasePlayer" and h:
            hash_offset.setdefault(h, off)

    ev_obj = build_evidence()
    ev = evidence_for_class(ev_obj, "BasePlayer")
    ev_by_name = aliases_for_class(ev_obj, "BasePlayer")

    _t, rows = baseplayer_fields(meta, ov_hashes)
    resolved, unresolved = [], []
    for r in rows:
        name = ov_hashes.get(r["hash"]) if r["hash"] else r["raw"]
        offs = set()
        if r["hash"] in hash_offset:
            offs.add(hash_offset[r["hash"]])
        elif name:
            offs |= ev_by_name.get(norm(name), set())
        if len(offs) == 1:
            off = next(iter(offs))
            ev_name = ev.get(off, (name, "", 0))[0] if off in ev else name
            resolved.append({
                "order": r["order"],
                "name": ev_name or name,
                "offset": off,
                "type": r["type"],
                "hash": r["hash"],
                "token": r["token"],
                "source": ("hash-slot" if r["hash"] in hash_offset
                           else "name-evidence"),
            })
        else:
            unresolved.append(r)

    os.makedirs(OUT, exist_ok=True)
    data = {
        "build": "26140533",
        "metadata_field_count": len(rows),
        "resolved": sorted(resolved, key=lambda x: x["offset"]),
        "unresolved_hashed": [
            {"order": r["order"], "hash": r["hash"], "type": r["type"]}
            for r in unresolved if r["hash"]],
        "unresolved_plaintext": [
            {"order": r["order"], "name": r["raw"], "type": r["type"]}
            for r in unresolved if not r["hash"]],
    }
    with open(os.path.join(OUT, "baseplayer_fields.json"), "w",
              encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2)

    # ---- requested header: evidence is authoritative for the offset,
    #      metadata supplies the type when the same slot was resolved
    by_name = {}
    for e in data["resolved"]:
        by_name.setdefault(norm(e["name"]), []).append(e)
    resolved_by_off = {e["offset"]: e for e in data["resolved"]}

    req_rows = []
    missing = []
    used_offsets = set()

    def best_type(off, e):
        meta_t = e["type"] if e else ""
        ev_t = ev.get(off, ("", "", 0))[1] or ""
        if ev_t and (not meta_t or meta_t.startswith("il2cpp_type")):
            return ev_t
        return meta_t or ev_t or "?"

    pending = []
    for canonical, aliases in REQUESTED:
        offs = set()
        for a in aliases:
            offs |= ev_by_name.get(norm(a), set())
        if len(offs) == 1:
            off = next(iter(offs))
            used_offsets.add(off)
            pending.append((canonical, off))
        else:
            pending.append((canonical, offs))

    for canonical, off in pending:
        if isinstance(off, int):
            e = resolved_by_off.get(off)
            req_rows.append({
                "name": canonical,
                "offset": off,
                "type": best_type(off, e),
                "hash": (e["hash"] if e else ""),
                "decrypt": DECRYPT_FOR.get(canonical, ""),
            })
            continue
        # ambiguous alias: drop offsets already claimed by a canonical field,
        # keep the remaining single candidate (BasePlayer+0x2F0 vs +0x6F8)
        left = set(off) - used_offsets
        if len(left) == 1:
            off = next(iter(left))
            used_offsets.add(off)
            e = resolved_by_off.get(off)
            req_rows.append({
                "name": canonical,
                "offset": off,
                "type": best_type(off, e),
                "hash": (e["hash"] if e else ""),
                "decrypt": DECRYPT_FOR.get(canonical, ""),
            })
        else:
            missing.append((canonical, sorted(off)))
    req_rows.sort(key=lambda x: x["offset"])

    dec = decryptor_map()
    lines = [
        "// ===========================================================================",
        "//  BasePlayer_offsets.h - reversed from Rust build 26140533",
        "//  generated by revers/rev_baseplayer.py - DO NOT EDIT BY HAND",
        "//",
        "//  Offsets are joined from live metadata + live/community evidence.",
        "//  `decrypt::` fields pass through the verified cipher in",
        "//  src/generated/Decryptors.generated.h (tools/reverse.py).",
        "// ===========================================================================",
        "#pragma once",
        "#include <cstdint>",
        "",
        "namespace BasePlayer {",
    ]
    for e in req_rows:
        note = f" // {e['type']}"
        if e["decrypt"]:
            note += f", decrypt::{e['decrypt']}"
        lines.append(
            f"    constexpr std::uintptr_t {e['name']:22s} = 0x{e['offset']:X};{note}")
    lines += ["}", ""]
    if dec:
        lines.append("namespace BasePlayerDecrypt { // GameAssembly RVAs")
        for e in req_rows:
            key = e["decrypt"]
            if key and key in dec:
                lines.append(
                    f"    constexpr std::uintptr_t {key:36s} = 0x{dec[key]:X};")
        lines += ["}", ""]
    with open(os.path.join(OUT, "BasePlayer_offsets.h"), "w",
              encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))

    rep = ["# BasePlayer reverse - build 26140533", ""]
    rep.append(f"- metadata fields: **{len(rows)}**")
    rep.append(f"- metadata rows bound to an offset: **{len(resolved)}**")
    rep.append(f"- unresolved hashed rows: **{len(data['unresolved_hashed'])}**")
    rep.append(f"- requested fields emitted: **{len(req_rows)} / {len(REQUESTED)}**")
    if missing:
        rep.append(f"- requested fields WITHOUT unique evidence: **{len(missing)}**")
    rep += ["", "## Requested fields", "",
            "| field | offset | type | decryptor |", "|---|---|---|---|"]
    for e in req_rows:
        rep.append(f"| `{e['name']}` | `0x{e['offset']:X}` | {e['type']} | "
                   f"{('`' + e['decrypt'] + '`') if e['decrypt'] else '-'} |")
    if missing:
        rep += ["", "## Requested but ambiguous", ""]
        for name, offs in missing:
            rep.append(f"- `{name}` -> candidates {[hex(o) for o in offs]}")
    rep += ["", "## Every metadata row bound to an offset", "",
            "| offset | field | type | hash slot |", "|---|---|---|---|"]
    for e in data["resolved"]:
        rep.append(f"| `0x{e['offset']:X}` | `{e['name']}` | {e['type']} | "
                   f"`%{(e['hash'] or '-')[:12]}` |")
    if unresolved:
        rep += ["", "## Unresolved (need a live dump or new evidence)", ""]
        for r in unresolved:
            rep.append(f"- ord {r['order']:3d}  `{r['raw'][:46]}`  type `{r['type']}`")
    with open(os.path.join(OUT, "baseplayer_report.md"), "w",
              encoding="utf-8", newline="\n") as f:
        f.write("\n".join(rep) + "\n")

    print(f"[+] BasePlayer metadata fields : {len(rows)}")
    print(f"[+] bound to offsets           : {len(resolved)}")
    print(f"[+] requested emitted          : {len(req_rows)}/{len(REQUESTED)}")
    if missing:
        print(f"[!] ambiguous requested       : {[m[0] for m in missing]}")
    for p in ("BasePlayer_offsets.h", "baseplayer_fields.json", "baseplayer_report.md"):
        print(f"[+] wrote {os.path.join(OUT, p)}")
    if dump_all:
        for e in req_rows:
            print(f"  0x{e['offset']:04X}  {e['name']:<24} {e['type']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
