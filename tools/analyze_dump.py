"""
Rust-Offset-Dumper post-processor.

Takes the live dump written by the injected DLL and turns it into compile-time
data for the next build of the dumper:

    %USERPROFILE%\\Desktop\\Rust-Offset-DumperDumps\\Rust-Offset-Dumper_offsets.h
    %USERPROFILE%\\Desktop\\Rust-Offset-DumperDumps\\Rust-Offset-Dumper_resolved.h
        -> src/generated/Offsets.generated.h   (regular gameplay offsets)
        -> tools/out/offsets.json / offsets_report.md

Only classes the dumper deliberately walks (Dumper.h: IsDumpClass) are
exported, and every value comes from il2cpp_field_get_offset / a verified
TypeInfo slot at dump time.  Nothing is typed in by hand.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GEN = os.path.join(ROOT, "src", "generated")
OUT = os.path.join(HERE, "out")

DEFAULT_DUMP = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop", "Rust-Offset-DumperDumps")

# must stay in sync with Dumper.h: IsDumpClass()
DUMP_CLASSES = {
    # entity tree / base
    "BaseNetworkable", "BaseEntity", "BaseCombatEntity", "BasePlayer",
    "BaseMountable", "BaseNpc", "BaseVehicle", "LocalPlayer", "GameManager",
    "ListComponent<Projectile>",
    # world items / containers
    "DroppedItem", "DroppedItemContainer", "WorldItem", "Item",
    "ItemContainer", "ItemDefinition", "ItemIcon", "ItemModProjectile",
    "ProjectileWeaponMod", "RecoilProperties", "HeldEntity", "ViewModel",
    "BaseViewModel", "StorageContainer", "LootContainer", "PlayerCorpse",
    "LootableCorpse", "HackableLockedCrate", "OreResourceEntity",
    "ResourceEntity", "CollectibleEntity", "GrowableEntity",
    # building / deployables
    "BuildingBlock", "BuildingPrivlidge", "Door", "Signage", "AutoTurret",
    "FlameTurret", "GunTrap", "TimedExplosive", "BaseLauncher",
    "BradleyAPC", "PatrolHelicopter",
    # player / combat
    "PlayerEyes", "PlayerModel", "PlayerInventory", "PlayerInput",
    "PlayerWalkMovement", "SkinnedMultiMesh", "AttackEntity", "BaseMelee",
    "BaseProjectile", "CompoundBowWeapon", "FlintStrikeWeapon",
    "Projectile", "HitTest",
    # camera / sky / statics
    "Camera", "MainCamera", "TOD_Sky", "TOD_CycleParameters",
    "TOD_DayParameters", "TOD_NightParameters", "ConVar.Graphics",
    "ConVar.Admin", "ConsoleSystem", "PhysX", "MapInterface",
}

RE_NS = re.compile(r"^\s*namespace\s+(\w+)\s*$")
RE_FIELD = re.compile(
    r"^\s*inline\s+constexpr\s+std::size_t\s+(\w+)\s*=\s*0x([0-9A-Fa-f]+)\s*;"
    r"(?:\s*//\s*(static|instance))?"
    r"(?:\s*\[(?:live\+table|table|live)\])?"
    r"(?:\s*\[%?([0-9A-Fa-f]{40})\])?")
RE_KLASS_COMMENT = re.compile(r"^\s*//\s*([\w:.%<>]+)\s+klass=0x([0-9A-Fa-f]+)")
RE_RES_KV = re.compile(r"^\s*static\s+constexpr\s+[\w:*]+\s+(\w+)\s*=\s*(.+?);")

# community name evidence (class+offset only, never a value source)
_refmod = None
try:
    import reference_parse as _refmod
    REF = _refmod.load()
except Exception:  # pragma: no cover - reference is optional
    REF = {"fields": {}, "hashed_classes": {}}


def deobf_class(name: str) -> str:
    if name.startswith("%"):
        return REF["hashed_classes"].get(name[1:].lower(), name)
    return name


def deobf_field(klass: str, name: str, offset: int) -> str:
    if not name.startswith("%") or _refmod is None:
        return name
    return _refmod.field_name(REF, klass, offset) or name


def _clean_name(n: str) -> str:
    """'Rust.UI::Thing' -> 'Thing'; obfuscated names stay as field_0x..."""
    return n.split("::")[-1]


def parse_offsets(path):
    classes = {}
    cur = None
    pending_name = None
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            m = RE_KLASS_COMMENT.match(line)
            if m:
                pending_name = m.group(1)
                continue
            m = RE_NS.match(line)
            if m:
                cur = {"ident": m.group(1),
                       "name": deobf_class(_clean_name(pending_name or m.group(1))),
                       "fields": []}
                classes[m.group(1)] = cur
                continue
            m = RE_FIELD.match(line)
            if m and cur is not None:
                off = int(m.group(2), 16)
                raw = f"%{m.group(4)}" if m.group(4) else m.group(1)
                cur["fields"].append({
                    "name": deobf_field(cur["name"], raw, off),
                    "offset": off,
                    "kind": m.group(3) or "instance",
                })
    return classes


def parse_resolved(path):
    out = {"classes": {}, "chain": {}}
    if not os.path.exists(path):
        return out
    cur = None
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            m = RE_NS.match(line)
            if m:
                name = m.group(1)
                if name == "entity_chain":
                    cur = out["chain"]
                elif name == "static_collections":
                    cur = None
                else:
                    cur = {}
                    out["classes"][name] = cur
                continue
            m = RE_RES_KV.match(line)
            if m and cur is not None:
                k, v = m.group(1), m.group(2)
                if v in ("true", "false"):
                    cur[k] = v == "true"
                elif v.startswith("0x"):
                    cur[k] = int(v, 16)
                elif v.startswith('"'):
                    cur[k] = v.strip('"')
    return out


def read_build(dumpdir: str) -> str:
    log = os.path.join(dumpdir, "Rust-Offset-Dumper_log.txt")
    try:
        with open(log, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                m = re.search(r"build tag:\s*(\d+)", line)
                if m:
                    return m.group(1)
    except OSError:
        pass
    return "unknown"


def sanitize(name: str) -> str:
    s = re.sub(r"[^0-9A-Za-z_]", "_", name)
    if not s or s[0].isdigit():
        s = "_" + s
    return s


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dumpdir", nargs="?", default=DEFAULT_DUMP)
    args = ap.parse_args()
    os.makedirs(GEN, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)

    off_path = os.path.join(args.dumpdir, "Rust-Offset-Dumper_offsets.h")
    res_path = os.path.join(args.dumpdir, "Rust-Offset-Dumper_resolved.h")
    if not os.path.exists(off_path):
        print(f"[!] no dump found: {off_path}")
        print("    inject Rust-Offset-Dumper.dll into RustClient.exe first (F8 = re-dump)")
        return 1

    classes = parse_offsets(off_path)
    resolved = parse_resolved(res_path)
    build = read_build(args.dumpdir)
    print(f"[+] parsed {len(classes)} classes from {off_path}")
    print(f"[+] build={build}  resolved classes={len(resolved['classes'])}")

    curated = {}
    for ident, c in classes.items():
        if c["name"] not in DUMP_CLASSES:
            continue
        # A slot with no readable name is not exported by the DLL anymore; keep
        # the guard here too so an old dump cannot reintroduce field_0xNNN.
        fields = [f for f in c["fields"]
                  if f["name"] and not f["name"].startswith("field_0x")
                  and not f["name"].startswith("%")]
        if not fields:
            continue
        curated[ident] = {"name": c["name"], "fields": fields}

    total = sum(len(c["fields"]) for c in curated.values())
    verified_ti = {n: v for n, v in resolved["classes"].items()
                   if v.get("typeinfo_verified") or v.get("typeinfo_seeded")
                   or v.get("typeinfo_computed")}

    # ---- generated header -------------------------------------------------
    L = []
    L.append("// ===========================================================================")
    L.append("//  Offsets.generated.h - AUTO-GENERATED by tools/analyze_dump.py")
    L.append(f"//  build: {build}")
    L.append(f"//  source: {off_path}")
    L.append("//")
    L.append("//  Every offset below was read from the live process with")
    L.append("//  il2cpp_field_get_offset / a verified TypeInfo slot.  DO NOT EDIT.")
    L.append("// ===========================================================================")
    L.append("#pragma once")
    L.append("#include <cstddef>")
    L.append("#include <cstdint>")
    L.append("")
    L.append(f'inline constexpr const char* Build = "{build}";')
    L.append("")
    L.append("namespace offsets_generated")
    L.append("{")
    L.append("    // Il2CppClass layout (name pointer at +0x10, static fields at +0xB8)")
    L.append("    namespace klass_layout")
    L.append("    {")
    L.append("        inline constexpr std::uintptr_t name_ptr = 0x10;")
    L.append("        inline constexpr std::uintptr_t static_fields = 0xB8;")
    L.append("    }")
    L.append("")
    if verified_ti:
        L.append("    // TypeInfo RVAs: slot(base + rva) == klass and klass+0x10 -> name")
        L.append("    namespace typeinfo")
        L.append("    {")
        for ident in sorted(verified_ti):
            v = verified_ti[ident]
            tag = ""
            if not v.get("typeinfo_verified") and v.get("typeinfo_seeded"):
                tag = " (seed; lazy TypeInfo token)"
            elif not v.get("typeinfo_verified") and v.get("typeinfo_computed"):
                tag = " (computed from metadata; lazy TypeInfo token)"
            L.append(f"        inline constexpr std::uintptr_t {sanitize(ident)} = "
                     f"0x{v['typeinfo_rva']:X}; // {ident}{tag}")
        L.append("    }")
        L.append("")
    if resolved["chain"].get("verified"):
        ch = resolved["chain"]
        L.append("    // verified BaseNetworkable static -> realm/list chain")
        L.append("    namespace entity_chain")
        L.append("    {")
        for name, key in (("realm_off", "realm_off"), ("list_off", "list_off"),
                          ("count_off", "count_off"), ("data_off", "data_off")):
            if key in ch:
                L.append(f"        inline constexpr std::uintptr_t {name} = 0x{ch[key]:X};")
        if "live_count" in ch:
            L.append(f"        inline constexpr std::uint32_t live_count = {ch['live_count']};")
        L.append("    }")
        L.append("")
    for ident in sorted(curated):
        c = curated[ident]
        L.append(f"    // {c['name']}")
        L.append(f"    namespace {sanitize(ident)}")
        L.append("    {")
        seen = set()
        for f in c["fields"]:
            nm = sanitize(f["name"])
            base = nm
            i = 1
            while nm in seen:
                i += 1
                nm = f"{base}_{i}"
            seen.add(nm)
            L.append(f"        inline constexpr std::size_t {nm} = 0x{f['offset']:X};"
                     f" // {f['kind']}")
        L.append("    }")
        L.append("")
    L.append("} // namespace offsets_generated")
    gen_path = os.path.join(GEN, "Offsets.generated.h")
    with open(gen_path, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")

    # ---- json + report ----------------------------------------------------
    payload = {"dumpdir": args.dumpdir, "build": build,
               "classes": curated, "resolved": resolved}
    with open(os.path.join(OUT, "offsets.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    rep = ["Rust-Offset-Dumper offsets report", "=" * 60,
           f"dump: {args.dumpdir}", f"build: {build}",
           f"classes total: {len(classes)}   curated: {len(curated)}   fields: {total}",
           f"typeinfo verified: {len(verified_ti)}", ""]
    if resolved["chain"].get("verified"):
        ch = resolved["chain"]
        rep.append("entity chain: VERIFIED")
        rep.append(f"  realm_off=0x{ch['realm_off']:X} list_off=0x{ch['list_off']:X} "
                   f"count_off=0x{ch['count_off']:X} data_off=0x{ch['data_off']:X} "
                   f"live_count={ch.get('live_count')} decryptor={ch.get('decryptor')}")
        rep.append("")
    for ident in sorted(curated):
        c = curated[ident]
        rep.append(c["name"])
        for f in c["fields"]:
            rep.append(f"  +0x{f['offset']:04X}  {f['kind']:8s} {f['name']}")
        rep.append("")
    with open(os.path.join(OUT, "offsets_report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(rep))

    print(f"[+] wrote {gen_path}")
    print(f"[+] wrote {os.path.join(OUT, 'offsets_report.md')}")
    print(f"[+] curated {len(curated)} classes / {total} fields / {len(verified_ti)} typeinfos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
