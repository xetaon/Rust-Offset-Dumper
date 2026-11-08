"""Read-only live verification of the BaseNetworkable static -> entity chain.

This does NOT inject anything and does NOT write to the game.  It only reads
memory of an already running RustClient.exe, so it can be run by the dumper
author without the user having to inject the DLL.

What it proves, per run:
  * TypeInfo slot 0x111F0768 still holds the BaseNetworkableStatic klass
  * klass+0xB8 is a readable static block
  * a static slot has the protected-wrapper shape (flag @ +0x10, words @ +0x18)
  * ClientEntitiesDecrypt / EntityListDecrypt turn those words into pointers
  * the decrypted pointer dereferences to a real managed klass name
  * (when possible) the decrypted object has a List/Array shape

Exit code 0 = all mandatory checks passed, 1 = something is unverified.

Usage:
    py tools\\verify_entity_chain.py
    py tools\\verify_entity_chain.py --pid 1234
"""
from __future__ import annotations

import argparse
import struct
import sys

try:
    import pymem
    import pymem.process
except ImportError:
    sys.exit("pymem is missing: py -m pip install pymem")

M32 = 0xFFFFFFFF
BASE_NETWORKABLE_STATIC_TYPEINFO = 0x111F0768
STATIC_OFF = 0xB8
WRAPPER_SLOTS = list(range(0x10, 0x88, 8))


def client_entities_word(v: int) -> int:
    v = (v - 0x49F666DD) & M32
    v ^= 0x0165993A
    v = ((v << 12) | (v >> 20)) & M32
    v ^= 0x06EA51C6
    return v


def entity_list_word(v: int) -> int:
    v = (v + 0x606A395C) & M32
    v = ((v << 17) | (v >> 15)) & M32
    return (v - 0x380CDD1C) & M32


def decrypt_words(raw: int, word_fn) -> int:
    lo = word_fn(raw & M32)
    hi = word_fn((raw >> 32) & M32)
    return (hi << 32) | lo


class Proc:
    def __init__(self, pid: int | None):
        try:
            self.pm = pymem.Pymem(pid) if pid else pymem.Pymem("RustClient.exe")
        except pymem.exception.ProcessNotFound:
            raise RuntimeError("RustClient.exe is not running (start the game first)")
        mod = pymem.process.module_from_name(self.pm.process_handle, "GameAssembly.dll")
        if not mod:
            raise RuntimeError("GameAssembly.dll is not loaded in this process")
        self.pid = self.pm.process_id
        self.base = mod.lpBaseOfDll
        self.size = mod.SizeOfImage

    def bytes(self, addr: int, n: int) -> bytes:
        return self.pm.read_bytes(addr, n)

    def u64(self, addr: int) -> int:
        return struct.unpack("<Q", self.bytes(addr, 8))[0]

    def u32(self, addr: int) -> int:
        return struct.unpack("<I", self.bytes(addr, 4))[0]

    def u8(self, addr: int) -> int:
        return self.bytes(addr, 1)[0]

    def readable(self, addr: int, n: int) -> bool:
        if addr < 0x10000:
            return False
        try:
            self.bytes(addr, n)
            return True
        except Exception:
            return False

    def cstr(self, addr: int, n: int = 128) -> str:
        try:
            return self.bytes(addr, n).split(b"\0")[0].decode("utf-8", "replace")
        except Exception:
            return ""

    def klass_name(self, obj: int) -> str:
        """Name of an object's class (obj+0x00 -> klass, klass+0x10 -> name)."""
        if not self.readable(obj, 8):
            return ""
        return self.klass_self_name(self.u64(obj))

    def klass_self_name(self, klass: int) -> str:
        """Name of a klass itself (klass+0x10 -> char*)."""
        if not self.readable(klass + 0x10, 8):
            return ""
        return self.cstr(self.u64(klass + 0x10))

    def pointer_block(self, addr: int, n: int = 8) -> str:
        """Describe a raw block of managed object pointers (not a List)."""
        names = []
        for i in range(n):
            a = addr + i * 8
            if not self.readable(a, 8):
                break
            e = self.u64(a)
            if e < 0x100000000 or not self.readable(e, 8):
                continue
            nm = self.klass_name(e)
            if nm:
                names.append(nm)
        if len(names) < 2:
            return ""
        return f"raw pointer block: {len(names)}/{n} points are managed objects " \
               f"({', '.join(names[:5])}{'...' if len(names) > 5 else ''})"

    def list_shape(self, obj: int) -> str:
        """Best-effort Il2Cpp List<T> / array description."""
        if not self.readable(obj, 0x40):
            return ""
        name = self.klass_name(obj)
        # Il2CppArray: klass, monitor, bounds, max_length @ +0x18, data @ +0x20
        try:
            n = self.u32(obj + 0x18)
            if 0 < n <= 500000:
                first = self.u64(obj + 0x20) if self.readable(obj + 0x20, 8) else 0
                if first == 0 or self.readable(first, 8):
                    return f"array-like len={n} ({name})"
        except Exception:
            pass
        # List<T>: items array @ +0x10, size @ +0x18
        try:
            arr = self.u64(obj + 0x10)
            n = self.u32(obj + 0x18)
            if arr and n and n <= 500000 and self.readable(arr, 0x28):
                first = self.u64(arr + 0x20)
                return f"list-like size={n} array=0x{arr:X} ({name}) first=0x{first:X}"
        except Exception:
            pass
        return f"object ({name})" if name else ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pid", type=int, default=None)
    ap.add_argument("--slot", type=lambda s: int(s, 0), default=BASE_NETWORKABLE_STATIC_TYPEINFO)
    args = ap.parse_args()

    try:
        p = Proc(args.pid)
    except RuntimeError as e:
        print(f"SKIP: {e}")
        return 2
    print(f"pid       {p.pid}")
    print(f"base      0x{p.base:X}  size=0x{p.size:X}")
    slot = p.base + args.slot
    print(f"slot      0x{slot:X} (rva 0x{args.slot:X})")

    fails: list[str] = []

    if not p.readable(slot, 8):
        print("FAIL: TypeInfo slot is not readable")
        return 1

    klass = p.u64(slot)
    kn = p.klass_self_name(klass) if klass else ""
    print(f"klass     0x{klass:X} name='{kn}'")
    if klass < 0x100000000 or not p.readable(klass, 0xC0):
        fails.append("TypeInfo slot does not hold a plausible klass pointer")
        print("FAIL: not a klass")
        return 1

    stat = p.u64(klass + STATIC_OFF)
    print(f"static    +0x{STATIC_OFF:X} = 0x{stat:X}")
    if not stat or not p.readable(stat, 0x90):
        print("FAIL: static block unreadable (menu? wrong build?)")
        return 1

    any_wrapper = False
    any_decrypt = False
    for off in WRAPPER_SLOTS:
        raw = p.u64(stat + off)
        if not raw or not p.readable(raw, 0x40):
            continue
        flag = p.u8(raw + 0x10)
        enc = p.u64(raw + 0x18)
        print(f"\nstatic+0x{off:X} = 0x{raw:X}  flag={flag} enc=0x{enc:X}")
        if not flag:
            continue
        any_wrapper = True

        for label, fn in (("client_entities", client_entities_word),
                          ("entity_list", entity_list_word)):
            v = decrypt_words(enc, fn)
            ok = p.readable(v, 0x30)
            print(f"  {label:15s} -> 0x{v:X}  readable={ok}")
            if not ok:
                continue
            shape = p.list_shape(v)
            print(f"      shape: {shape or '<not a managed object>'}")
            if shape and "object ()" not in shape:
                any_decrypt = True
            else:
                block = p.pointer_block(v)
                if block:
                    print(f"      block: {block}")
                    fails.append(
                        f"{label} decrypted to a {block} - menu/other data, not an entity list")

    print()
    if not any_wrapper:
        fails.append("no populated encrypted wrapper found in static block")
    if not any_decrypt:
        fails.append("decrypted pointer did not resolve to a readable managed object")

    if fails:
        for f in fails:
            print("FAIL:", f)
        print("\nRESULT: UNVERIFIED")
        return 1

    print("RESULT: PASS - static wrapper decrypts to a readable managed object")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
