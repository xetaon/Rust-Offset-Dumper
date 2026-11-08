#!/usr/bin/env python3
"""
run_all.py - run the whole static reverse pipeline and copy the artifacts
into revers/out/ so this folder is self-contained.

Steps:
  1. tools/reverse.py            -> regenerate + verify Decryptors.generated.h
                                    against the installed GameAssembly.dll
  2. revers/rev_baseplayer.py    -> BasePlayer offsets/decrypts
  3. tools/analyze_dump.py       -> (only if a live dump exists) refresh
                                    src/generated/Offsets.generated.h

Usage:
    py -3 revers\\run_all.py
    py -3 revers\\run_all.py --fast   # skip the full decryptor census
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOOLS = os.path.join(ROOT, "tools")
OUT = os.path.join(HERE, "out")
PY = sys.executable or "py"


def run(script, *args):
    cmd = [PY, script, *args]
    print(f"[run] {' '.join(os.path.relpath(c, ROOT) if os.path.isabs(c) else c for c in cmd)}")
    return subprocess.run(cmd, cwd=ROOT).returncode


def copy(src, dst):
    if os.path.exists(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        print(f"[cp ] {os.path.relpath(src, ROOT)} -> {os.path.relpath(dst, ROOT)}")


def main():
    args = sys.argv[1:]
    fast = "--fast" in args
    os.makedirs(OUT, exist_ok=True)

    rc = 0
    rev_args = ["--known-only"] if fast else []
    rc |= run(os.path.join(TOOLS, "reverse.py"), *rev_args)
    copy(os.path.join(TOOLS, "out", "decryptors.txt"),
         os.path.join(OUT, "decryptors.txt"))
    copy(os.path.join(TOOLS, "out", "decryptors.json"),
         os.path.join(OUT, "decryptors.json"))

    rc |= run(os.path.join(HERE, "rev_baseplayer.py"), "--all")
    rc |= run(os.path.join(HERE, "rev_classes.py"))
    # dump-free, GameAssembly-only pipeline (authoritative for offsets)
    rc |= run(os.path.join(HERE, "rev_binary.py"))

    dump = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop",
                        "Rust-Offset-DumperDumps", "Rust-Offset-Dumper_offsets.h")
    if os.path.exists(dump):
        rc |= run(os.path.join(TOOLS, "analyze_dump.py"))
        copy(os.path.join(ROOT, "src", "generated", "Offsets.generated.h"),
             os.path.join(OUT, "Offsets.generated.snapshot.h"))
    else:
        print("[skip] no live dump at "
              f"{os.path.relpath(dump, os.path.expanduser('~'))} "
              "- inject Rust-Offset-Dumper.dll and press F8 for a fresh live pass")

    print("\n[done] artifacts in revers/out:")
    for name in sorted(os.listdir(OUT)):
        print(f"   {name}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
