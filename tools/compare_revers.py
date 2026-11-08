#!/usr/bin/env python3
"""Compare the live dump against the static proof from revers/out.

Source of truth: revers/out/*_binary.h (revers/rev_binary.py - every value is
backed by the .rdata offset table or a `[this+disp]` operand in GameAssembly).
Target:          src/generated/Offsets.generated.h (live il2cpp + verified
                 .rdata table, written by tools/analyze_dump.py).

For every field of the four proof classes it prints OK / MISSING / MISMATCH.
A MISSING line means the live dump did not export the slot at all; a MISMATCH
means both sides have the field but the offsets disagree.

Usage:
    py -3 tools\\compare_revers.py
    py -3 tools\\compare_revers.py --live src\\generated\\Offsets.generated.h
"""
from __future__ import annotations

import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REVERS_OUT = os.path.join(ROOT, "revers", "out")
DEFAULT_LIVE = os.path.join(ROOT, "src", "generated", "Offsets.generated.h")

CLASSES = ("BasePlayer", "Projectile", "AttackEntity", "PlayerModel")

RE_PROOF = re.compile(
    r"^\s*constexpr\s+std::uintptr_t\s+(\w+)\s*=\s*0x([0-9A-Fa-f]+)\s*;")
RE_LIVE_NS = re.compile(r"^\s*namespace\s+(\w+)\s*$")
RE_LIVE_FIELD = re.compile(
    r"^\s*inline\s+constexpr\s+std::size_t\s+(\w+)\s*=\s*0x([0-9A-Fa-f]+)\s*;")


def parse_proof(path):
    out = {}
    for line in open(path, "r", encoding="utf-8", errors="ignore"):
        m = RE_PROOF.match(line)
        if m:
            out[m.group(1)] = int(m.group(2), 16)
    return out


def parse_live(path):
    classes = {}
    cur = None
    for line in open(path, "r", encoding="utf-8", errors="ignore"):
        m = RE_LIVE_NS.match(line)
        if m:
            cur = m.group(1)
            classes.setdefault(cur, {})
            continue
        m = RE_LIVE_FIELD.match(line)
        if m and cur:
            classes[cur][m.group(1)] = int(m.group(2), 16)
    return classes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", default=DEFAULT_LIVE)
    ap.add_argument("--revers", default=REVERS_OUT)
    args = ap.parse_args()

    if not os.path.exists(args.live):
        print(f"[!] no live header: {args.live}")
        print("    inject Rust-Offset-Dumper.dll (F8), then: py tools\\analyze_dump.py")
        return 1

    live = parse_live(args.live)
    print(f"[+] live header: {args.live}")
    print(f"[+] proof dir  : {args.revers}")
    print()

    totals = {"OK": 0, "MISSING": 0, "MISMATCH": 0}
    failed = 0

    for cls in CLASSES:
        proof_path = os.path.join(args.revers, f"{cls}_binary.h")
        if not os.path.exists(proof_path):
            print(f"[!] no proof for {cls}: {proof_path}")
            failed += 1
            continue

        proof = parse_proof(proof_path)
        got = live.get(cls, {})

        ok, missing, mismatch = [], [], []
        for name, off in proof.items():
            if name not in got:
                missing.append((name, off))
            elif got[name] != off:
                mismatch.append((name, off, got[name]))
            else:
                ok.append(name)

        totals["OK"] += len(ok)
        totals["MISSING"] += len(missing)
        totals["MISMATCH"] += len(mismatch)

        status = "OK" if not missing and not mismatch else "INCOMPLETE"
        print(f"{cls:<14} {status:<11} "
              f"proof={len(proof):<4} live={len(got):<4} "
              f"ok={len(ok):<4} missing={len(missing):<3} mismatch={len(mismatch)}")
        for name, off in sorted(missing, key=lambda x: x[1]):
            print(f"    MISSING   {name:<48} 0x{off:X}")
        for name, want, have in sorted(mismatch, key=lambda x: x[1]):
            print(f"    MISMATCH  {name:<48} proof=0x{want:X} live=0x{have:X}")
        if missing:
            print("    hint: MISSING here means the live walk never exported the slot "
                  "(check [CLASS][!] field walk FAULT in Rust-Offset-Dumper_log.txt).")
        print()

    print(f"totals: OK={totals['OK']}  MISSING={totals['MISSING']}  "
          f"MISMATCH={totals['MISMATCH']}")
    return 1 if (totals["MISSING"] or totals["MISMATCH"] or failed) else 0


if __name__ == "__main__":
    sys.exit(main())
