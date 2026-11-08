#!/usr/bin/env python3
"""
offsets_match.py - cross-reference an OLD (unobfuscated) offsets header against
a FRESH Rust-Offset-Dumper_classes.txt dump.

Why this exists
---------------
A live Rust build partially protects its metadata:
  * some field names are replaced with %<sha1>,
  * some field descriptors report the poison offset 0x67676767,
  * method tables come back empty.

The old header still carries the human names.  It does NOT carry usable offsets:
between two Rust builds field offsets drift by hundreds of bytes and the field
ORDER inside a class can change, so nothing here is ever copied blindly.  The
tool only produces:
  * anchors      - fields whose name survived live, with the live offset + delta
  * gaps         - live slots without a name, between which anchors they sit
  * missing      - old fields that did not survive live
That output is the input for runtime verification (see the note at the end).

Usage:
    py -3 tools/offsets_match.py --old old_offsets.h \
                                --new Rust-Offset-DumperDumps/Rust-Offset-Dumper_classes.txt \
                                --out Rust-Offset-DumperDumps/Rust-Offset-Dumper_name_map.txt
"""

import argparse
import collections
import re
import sys

POISON = 0x67676767

OLD_NS_RE = re.compile(r"^\s*namespace\s+(\w+)\s*\{")
OLD_FIELD_RE = re.compile(r"^\s*constexpr\s+auto\s+(\w+)\s*=\s*(0x[0-9a-fA-F]+)\s*;")
NEW_CLASS_RE = re.compile(r"^class\s+(.+?)\s*$")
NEW_FIELD_RE = re.compile(r"^\s*\+0x([0-9a-fA-F]+)\s+(instance|static)\s+(\S+)(?:\s+:\s+(.*?))?\s*$")


def parse_old(path):
    """-> {class: {field: offset}} for fields (offset < 0x10000)."""
    out = collections.defaultdict(dict)
    cur = None
    for line in open(path, encoding="utf-8", errors="replace"):
        m = OLD_NS_RE.match(line)
        if m:
            cur = m.group(1)
            continue
        if cur is None:
            continue
        m = OLD_FIELD_RE.match(line)
        if m:
            name, val = m.group(1), int(m.group(2), 16)
            if val < 0x10000:
                out[cur][name] = val
    return out


def parse_new(path):
    """-> ordered list of class blocks: {name, short, fields:[(off,kind,name,type)]}"""
    blocks = []
    cur = None
    for line in open(path, encoding="utf-8", errors="replace"):
        m = NEW_CLASS_RE.match(line)
        if m:
            full = m.group(1)
            cur = {"name": full, "short": full.split("::")[-1], "fields": []}
            blocks.append(cur)
            continue
        m = NEW_FIELD_RE.match(line)
        if m and cur is not None:
            cur["fields"].append((int(m.group(1), 16), m.group(2), m.group(3),
                                  (m.group(4) or "").strip()))
    return blocks


def pick_block(old_name, blocks):
    """Several assemblies may declare the same short name; pick the block that
    shares the most field names with the old header (ties -> most fields)."""
    cands = [b for b in blocks if b["short"] == old_name]
    if not cands:
        return None
    old_fields = _OLD_CACHE.get(old_name, {})
    best, best_score = None, (-1, -1)
    for b in cands:
        live = {f[2] for f in b["fields"]}
        score = (len(live & set(old_fields)), len(b["fields"]))
        if score > best_score:
            best, best_score = b, score
    return best


_OLD_CACHE = {}


def is_hash(name):
    return name.startswith("%")


def analyze(old, blocks):
    _OLD_CACHE.clear()
    _OLD_CACHE.update(old)

    report = []
    summary = {"classes": 0, "old_fields": 0, "live_fields": 0,
               "anchors": 0, "gaps": 0, "missing": 0, "poison": 0,
               "classes_found": 0}

    for old_name in sorted(old):
        ofields = old[old_name]
        if not ofields:
            continue
        block = pick_block(old_name, blocks)
        summary["classes"] += 1
        summary["old_fields"] += len(ofields)
        if block is None:
            report.append((old_name, None, [], [], sorted(ofields), 0))
            summary["missing"] += len(ofields)
            continue
        summary["classes_found"] += 1
        summary["live_fields"] += len(block["fields"])

        live_by_name = {f[2]: f[0] for f in block["fields"] if not is_hash(f[2])}
        live_types = {f[2]: f[3] for f in block["fields"]}

        anchors = []
        for name, off in sorted(ofields.items(), key=lambda kv: kv[1]):
            if name in live_by_name:
                live_off = live_by_name[name]
                anchors.append((name, off, live_off, live_off - off,
                                live_types.get(name, "")))
        summary["anchors"] += len(anchors)

        anchored = {a[0] for a in anchors}
        missing = sorted(n for n in ofields if n not in anchored)
        summary["missing"] += len(missing)

        # live slots without a usable name, annotated with the nearest anchors
        gaps = []
        named_live = sorted((f[0], f[2], f[3]) for f in block["fields"]
                            if not is_hash(f[2]))
        for off, kind, name, ty in sorted(block["fields"]):
            if not is_hash(name):
                continue
            prev = ["%s@0x%X" % (n, o) for o, n, _ in named_live if o < off][-1:]
            nxt = ["%s@0x%X" % (n, o) for o, n, _ in named_live if o > off][:1]
            gaps.append((off, kind, name, ty, prev[0] if prev else "-",
                         nxt[0] if nxt else "-"))
        summary["gaps"] += len(gaps)

        report.append((old_name, block, anchors, gaps, missing,
                       len(block["fields"])))
    return report, summary


def write_report(path, report, summary, old_path, new_path):
    f = open(path, "w", encoding="utf-8")
    w = f.write
    w("Rust-Offset-Dumper old->live name map\n")
    w("old: %s\nnew: %s\n\n" % (old_path, new_path))
    w("%d old class(es), %d field(s); %d matched to a live class, "
      "%d anchor(s) by name, %d live hashed slot(s), %d old field(s) not present live.\n\n"
      % (summary["classes"], summary["old_fields"], summary["classes_found"],
         summary["anchors"], summary["gaps"], summary["missing"]))
    w("NOTE: offsets below are MEASURED live values. `delta` is only diagnostic -\n")
    w("never apply it to another field, and never copy an old offset into a cheat.\n")
    w("=" * 78 + "\n\n")

    for old_name, block, anchors, gaps, missing, live_total in report:
        w("== %s ==\n" % old_name)
        if block is None:
            w("  NOT FOUND in the live dump\n")
            for n in missing:
                w("    - %s\n" % n)
            w("\n")
            continue
        w("  live class: %s  fields=%d  anchors=%d  unnamed=%d\n"
          % (block["name"], live_total, len(anchors), len(gaps)))
        if anchors:
            w("  -- anchors (name survived live) --\n")
            for name, old_off, live_off, delta, ty in anchors:
                w("    %-34s old=0x%03X live=0x%03X delta=%+5d%s\n"
                  % (name, old_off, live_off, delta,
                     ("  : " + ty) if ty else ""))
        if gaps:
            w("  -- live slots without a name --\n")
            for off, kind, name, ty, prev, nxt in gaps:
                w("    +0x%03X %-8s %s  type=%s  after %s  before %s\n"
                  % (off, kind, name, ty or "?", prev, nxt))
        if missing:
            w("  -- old fields not found by name live (need runtime verification) --\n")
            for n in missing:
                w("    - %s (old 0x%X)\n" % (n, _OLD_CACHE[old_name][n]))
        w("\n")
    f.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", required=True, help="old unobfuscated offsets header")
    ap.add_argument("--new", required=True, help="fresh Rust-Offset-Dumper_classes.txt")
    ap.add_argument("--out", default="", help="report path (default: stdout)")
    a = ap.parse_args()

    old = parse_old(a.old)
    blocks = parse_new(a.new)
    if not old:
        print("no field offsets parsed from %s" % a.old, file=sys.stderr)
        return 2
    if not blocks:
        print("no classes parsed from %s" % a.new, file=sys.stderr)
        return 2

    report, summary = analyze(old, blocks)
    if a.out:
        write_report(a.out, report, summary, a.old, a.new)
        print("wrote %s" % a.out)
    else:
        for old_name, block, anchors, gaps, missing, _ in report:
            print("%-24s live=%-5s anchors=%3d unnamed=%3d missing=%3d"
                  % (old_name, "yes" if block else "NO", len(anchors),
                     len(gaps), len(missing)))
    print("\n%d/%d old classes found live, %d/%d old fields matched by name, "
          "%d live hashed slots"
          % (summary["classes_found"], summary["classes"],
             summary["anchors"], summary["old_fields"], summary["gaps"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
