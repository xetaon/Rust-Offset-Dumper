"""Parse the cheatoffsets raw text dump into (class, offset) -> field name.

The text file is a community offsets paste for build 26140533.  It is only used
as *name* evidence: every offset is still checked against the live dump by
analyze_dump.py before it is emitted.
"""
from __future__ import annotations

import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "reference", "cheatoffsets_26140533.txt")

RE_SECTION = re.compile(r"^##\s+(.+?)\s*$", re.M)
RE_CONST = re.compile(
    r"inline\s+static\s+constexpr\s+uintptr_t\s+(\w+)\s*=\s*0x([0-9A-Fa-f]+)\s*;")


def load():
    text = open(RAW, "r", encoding="utf-8", errors="ignore").read()

    # hashed class map: real_name %hash
    hashed_classes = {}
    m = re.search(r"## hashed klasses\s*```(.*?)```", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            parts = line.split()
            if len(parts) == 2 and parts[1].startswith("%"):
                hashed_classes[parts[1][1:].lower()] = parts[0]

    # field tables: section name == class name, constants inside
    fields = {}          # class -> {offset: name}
    classes = {}         # lower -> canonical
    for m in RE_SECTION.finditer(text):
        name = m.group(1).strip()
        start = m.end()
        nxt = text.find("\n## ", start)
        body = text[start:nxt if nxt >= 0 else len(text)]
        if "inline static constexpr uintptr_t" not in body:
            continue
        vals = {}
        for cm in RE_CONST.finditer(body):
            vals[int(cm.group(2), 16)] = cm.group(1)
        if not vals:
            continue
        key = re.sub(r"[^a-z0-9]", "", name.lower())
        classes.setdefault(key, name)
        fields.setdefault(name, {}).update(vals)

    # build info TypeInfo list
    typeinfos = {}
    for tm in re.finditer(r"([\w:. ]+?)\s+TypeInfo:\s*0x([0-9A-Fa-f]+)", text):
        typeinfos[tm.group(1).strip()] = int(tm.group(2), 16)

    return {"hashed_classes": hashed_classes, "fields": fields,
            "classes": classes, "typeinfos": typeinfos, "text": text}


def field_name(ref, klass, offset):
    """Return a reference name for klass+offset, tolerating namespace prefixes."""
    k = re.sub(r"[^a-z0-9]", "", klass.lower())
    for name, vals in ref["fields"].items():
        if re.sub(r"[^a-z0-9]", "", name.lower()) == k:
            return vals.get(offset)
    return None


if __name__ == "__main__":
    r = load()
    print("hashed classes:", len(r["hashed_classes"]))
    print("field classes:", len(r["fields"]),
          "offsets:", sum(len(v) for v in r["fields"].values()))
    print("typeinfos:", r["typeinfos"])
    for k in ("BasePlayer", "PlayerWalkMovement", "TOD_Sky", "TodSky", "MainCamera"):
        print(k, len(r["fields"].get(k, {})), sorted(r["fields"].get(k, {}))[:6])
