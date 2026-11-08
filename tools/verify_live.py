"""
Live verification of TypeInfo RVA slots against the running Rust client.

The reference header (build 26140533) lists class TypeInfo RVAs.  A TypeInfo RVA
is only trustworthy if

    slot = GameAssembly + rva  ->  klass
    klass + 0x10               ->  printable class name

This tool reads the live process (read-only) and checks exactly that, so we
never hardcode a slot that points at garbage / another class.

Usage:
    py tools/verify_live.py                 # auto-detect RustClient pid
    py tools/verify_live.py --pid 7640
    py tools/verify_live.py --json tools/out/typeinfo_live.json
"""
from __future__ import annotations

import argparse
import json
import os
import struct
import sys

import pymem

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

# name -> TypeInfo RVA  (from the reference header, build 26140533)
TYPEINFO = {
    "BaseNetworkable": 0x111F0768,
    "BaseEntity": 0x1129D198,
    "BaseCombatEntity": 0x1129D170,
    "BasePlayer": 0x111FFDF0,
    "BaseNpc": 0x111FC768,
    "BaseVehicle": 0x1120D288,
    "DroppedItemContainer": 0x111C0478,
    "OreResourceEntity": 0x11253298,
    "CollectibleEntity": 0x11253330,
    "BuildingBlock": 0x111A27D0,
    "BuildingPrivlidge": 0x111E7600,
    "Door": 0x111D3A40,
    "WorldItem": 0x111BEDB0,
    "Signage": 0x11183B28,
    "MainCamera": 0x111C43A0,
    "ListComponent<Projectile>": 0x11204AF0,
    "PlayerEyes": 0x111C00E0,
    "PlayerModel": 0x111851B0,
    "TOD_Sky": 0x11235250,
    "Item": 0x11282E80,
    "ConsoleSystem.Command": 0x111AF278,
    "PlayerInventory": 0x111C2C80,
    "PlayerInput": 0x1122D2A0,
    "BaseProjectile": 0x11181BA8,
    "HeldEntity": 0x112957D0,
    "BaseViewModel": 0x111F9500,
    "AutoTurret": 0x111E5910,
    "GameManager_Static": 0x11181780,
    "PhysX": 0x11203D68,
    "ItemIcon": 0x11236AC0,
    "LocalPlayer": 0x111E9EE0,
    "MapInterface": 0x1120D750,
    "ConVar.Graphics": 0x111F03E0,
    "ConVar.Admin": 0x11239810,
    "SingletonComponent<UI_LoadingScreen>": 0x111AFA80,
    "SingletonComponent<MixerSnapshotManager>": 0x11224E80,
}


def read_cstr(pm: pymem.Pymem, addr: int, limit: int = 256) -> str:
    try:
        raw = pm.read_bytes(addr, limit)
    except Exception:
        return ""
    end = raw.find(b"\0")
    if end >= 0:
        raw = raw[:end]
    return raw.decode("latin1", "replace")


def read_u64(pm: pymem.Pymem, addr: int) -> int:
    return struct.unpack("<Q", pm.read_bytes(addr, 8))[0]


def klass_name(pm: pymem.Pymem, klass: int) -> str:
    """Il2CppClass::name is a pointer at +0x10 on this build."""
    try:
        name_ptr = read_u64(pm, klass + 0x10)
        if name_ptr < 0x10000:
            return ""
        return read_cstr(pm, name_ptr)
    except Exception:
        return ""


def find_pid() -> int:
    try:
        return pymem.process.process_from_name("RustClient.exe")
    except Exception:
        return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pid", type=int, default=0)
    ap.add_argument("--json", default=os.path.join(OUT, "typeinfo_live.json"))
    args = ap.parse_args()

    pid = args.pid or find_pid()
    if not pid:
        print("[!] RustClient.exe is not running - start the game first")
        return 1

    pm = pymem.Pymem(pid)
    base = pymem.process.module_from_name(pm.process_handle, "GameAssembly.dll").lpBaseOfDll
    print(f"[+] pid={pid}  GameAssembly=0x{base:X}")

    results = []
    ok = bad = 0
    for name, rva in TYPEINFO.items():
        slot = base + rva
        entry = {"name": name, "rva": rva, "slot": slot}
        try:
            klass = read_u64(pm, slot)
        except Exception:
            klass = 0
        entry["klass"] = klass
        if klass < 0x10000:
            entry["status"] = "empty"
            bad += 1
            print(f"[EMPTY] {name:42s} rva=0x{rva:X}  slot -> 0x{klass:X}")
        else:
            live = klass_name(pm, klass)
            entry["live_name"] = live
            expect = name.split("<")[0].split(".")[-1].replace("_Static", "")
            # reference names are not always exact CLR names; accept a prefix or
            # the mapped MainCamera -> Camera case
            cands = {expect}
            if expect == "MainCamera":
                cands.add("Camera")
            if expect == "GameManager":
                cands.add("GameManager")
            good = live in cands or any(live.startswith(c) for c in cands)
            entry["status"] = "ok" if good else "name-mismatch"
            if good:
                ok += 1
                print(f"[ OK  ] {name:42s} rva=0x{rva:X}  klass=0x{klass:X}  name='{live}'")
            else:
                bad += 1
                print(f"[NAME?] {name:42s} rva=0x{rva:X}  klass=0x{klass:X}  name='{live}'")
        results.append(entry)

    payload = {"pid": pid, "game_assembly": base, "results": results}
    os.makedirs(OUT, exist_ok=True)
    with open(args.json, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"\n[+] verified {ok}/{len(results)} TypeInfo slots, problems: {bad}")
    print(f"[+] wrote {args.json}")
    return 0 if bad == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
