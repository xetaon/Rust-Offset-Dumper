"""
Instant Loot reverse - artifact generator (Rust build 26140533).

Writes into Rust-Offset-Dumper/revers/out:
  loot_offsets.json            confirmed fields / RVAs and where each came from
  loot_disasm_OnClicked.txt    full disassembly of LootAllButton::OnClicked
  loot_report.md               human-readable summary

Everything here is read from the local GameAssembly.dll - no game process,
no build of the cheat.
"""
from __future__ import annotations

import json
import os
import sys

import capstone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rev_loot import Pe, DLL  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

ONCLICKED = 0x463DB40
ITEM_MOVE = 0x1834DB0          # called once per ItemIcon by OnClicked
TRYTOMOVE_CLOSURE = 0x185C650  # <TryToMove>b__0 (already known from the dump)

CONFIRMED = {
    "build": "26140533",
    "source": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Rust\\GameAssembly.dll",
    "fields": {
        "PlayerInventory.loot": {"offset": "0x48", "type": "PlayerLoot"},
        "PlayerLoot.entitySource": {"offset": "0x28", "type": "BaseEntity"},
        "LootAllButton.inventoryGrid": {"offset": "0x28", "type": "Rust.UI.InventoryGrid"},
    },
    "methods": {
        "LootAllButton.OnClicked": {"rva": "0x463DB40", "token": "0x0602a4dc", "args": ["this"], "returns": "void"},
        "LootAllButton.Awake": {"rva": "0x463DDD0", "token": "0x0602a4de",
                                "note": "plaintext name; builds the [this+0x20] predicate"},
        "LootAllButton..ctor": {"rva": "0x9CB140", "token": "0x0602a4dd"},
        "ItemIcon.TryToMove (parent, unconfirmed name)": {"rva": "0x1834DB0",
                                                          "note": "called by OnClicked per grid item; blob 0x1834DB0..0x1835308"},
        "ItemIcon.<TryToMove>b__0 closure": {"rva": "0x185C650", "note": "from the original dump"},
    },
    "evidence": {
        "OnClicked_grid_read": "0x463DBA6  mov rbx, qword ptr [rsi + 0x28]",
        "OnClicked_item_move_call": "0x463DD32  call 0x1834DB0",
        "PlayerInventory.loot": "metadata field #4 'loot'; reference names_extra.txt:805 + offsets.json (offset 72)",
        "PlayerLoot.entitySource": "metadata field #0 'entitySource'; reference names_extra.txt:810 (+0x28)",
        "LootAllButton.fields": "metadata: field #0 hashed, field #1 'inventoryGrid' -> +0x20 / +0x28",
        "LootAllButton.methods": "metadata type 6156 token 0x0200180d: OnClicked, .ctor, Awake only",
        "log_proof": "[LOOT] poll onClicked = module base + 0x463DB40 but btn=0 on all 11 polls",
    },
}


def disasm_fn(pe, rva, limit_bytes=None):
    funcs = pe.functions()
    hit = [f for f in funcs if f[0] <= rva < f[1]]
    if not hit:
        return "0x%X not present in .pdata\n" % rva
    b, e = hit[0]
    n = min(e - b, limit_bytes) if limit_bytes else (e - b)
    code = pe.read(b, n)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    lines = ["; function 0x%X..0x%X len 0x%X" % (b, e, e - b)]
    for ins in md.disasm(code, b):
        lines.append("0x%08X  %-24s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    return "\n".join(lines) + "\n"


def main():
    pe = Pe(DLL)
    confirmed = dict(CONFIRMED)
    confirmed["image_base"] = "0x%X" % pe.image_base
    confirmed["dll_size"] = os.path.getsize(DLL)

    with open(os.path.join(OUT, "loot_offsets.json"), "w", encoding="utf-8") as f:
        json.dump(confirmed, f, indent=2)

    for name, rva in (("OnClicked", ONCLICKED), ("item_move_1834DB0", ITEM_MOVE),
                      ("TryToMove_closure_185C650", TRYTOMOVE_CLOSURE)):
        with open(os.path.join(OUT, "loot_disasm_%s.txt" % name), "w", encoding="utf-8") as f:
            f.write(disasm_fn(pe, rva))

    md = []
    md.append("# Instant Loot - reverse report (Rust 26140533)\n")
    md.append("Source: `%s`\n" % DLL)
    md.append("ImageBase: 0x%X  size %d\n" % (pe.image_base, os.path.getsize(DLL)))
    md.append("\n## Confirmed layout\n")
    md.append("| symbol | value | evidence |")
    md.append("|---|---|---|")
    for k, v in confirmed["fields"].items():
        md.append("| %s | %s | %s |" % (k, v["offset"], v["type"]))
    for k, v in confirmed["methods"].items():
        md.append("| %s | %s | %s |" % (k, v["rva"], v.get("note", "disassembly")))
    md.append("\n## Why the current Instant Loot is dead\n")
    md.append("`[LOOT] poll` in the runtime log shows, on all 11 heartbeats:\n")
    md.append("```")
    md.append("loot=0x115F12FD960 ent=0x0 session=0x0 btn=0x0")
    md.append("onClicked=0x7FF967CFDB40   (= module base + 0x463DB40)")
    md.append("```")
    md.append("So `OnClicked` **was** resolved, and the code pointer is right. The")
    md.append("failure is the class/instance path, not the method:\n")
    md.append("1. At injection `LootAllButton` and `OnClicked` resolved (hence the")
    md.append("   correct RVA in every poll).")
    md.append("2. Afterwards the lazy resolver in `Interact.h` uses its own static")
    md.append("   and asks for the class again. On this build EAC clobbers metadata")
    md.append("   names after injection, so that later lookup can return 0. Once it")
    md.append("   does, `s_lootAllKlass` stays 0 for the rest of the session.")
    md.append("3. The instance scan is gated on `s_lootAllKlass`, so a 0 there means")
    md.append("   the scan never runs at all. The log contains no `[LOOT] awake:`")
    md.append("   and no `[LOOT] rediscover:` lines, i.e. neither the Awake hook nor")
    md.append("   the scene scan ever produced an instance.")
    md.append("4. `lootBtn` therefore stayed 0 and")
    md.append("   `canButton = lootSession && lootBtn && onClicked && gridOk` could")
    md.append("   never be true, so the game's own loot-all was never invoked.")
    md.append("")
    md.append("The old code also had a one-shot class latch in `Hook.h`, a hard")
    md.append("1000-try latch on the scan, a 10 s idle scan interval and a trigger")
    md.append("gated on `entitySource`. Any one of those turns a single transient")
    md.append("resolution miss into a dead feature for the whole session. That is")
    md.append("exactly the symptom here.")
    md.append("")
    md.append("`ent=0x0` is consistent with the panel being closed at the poll")
    md.append("instants; it is not the primary failure. The offsets are correct:")
    md.append("- `OnClicked` reads the grid at `this+0x28` (`0x463DBA6`).")
    md.append("- It calls the per-item move routine at `0x1834DB0` (`0x463DD32`).")
    md.append("- metadata confirms `LootAllButton` field #1 is `inventoryGrid` and")
    md.append("  `PlayerLoot` field #0 is `entitySource` (`revers/dump_fields.py`).\n")

    md.append("## OnClicked internals (verified)\n")
    md.append("`LootAllButton::OnClicked` RVA `0x463DB40`, body `0x463DB40..0x463DDC2`:\n")
    md.append("1. `0x463DBA6  mov rbx, [rsi+0x28]` - load `this.inventoryGrid`;")
    md.append("   `0x463DBAD je 0x463DDBC` - null grid raises the game's NRE.")
    md.append("2. Builds the grid enumerator (`call 0x869FA0`, `call 0x7E0E0`) and loops.")
    md.append("3. For each element resolves a virtual/interface call through the")
    md.append("   klass vtable (`[klass+0x12e]` count, `[klass+0xb0]` slots, `+0x138`).")
    md.append("4. `0x463DCFB  mov rdx, [rax+0x160]` - reads the item component; skip if 0.")
    md.append("5. `0x463DD0B  cmp qword [rsi+0x20], 0` - optional button-side predicate;")
    md.append("   when set it must return true (`call [r9+0x18]`).")
    md.append("6. `0x463DD32  call 0x1834DB0` with `rcx=item`, `dl=1` - move this item.\n")
    md.append("`0x1834DB0` is a shared UI move routine (contiguous COMDAT blob")
    md.append("`0x1834DB0..0x1835308`; `.pdata` splits it into 5 entries, so a naive")
    md.append("enclosing-function lookup truncates it). It reads `[this+0x160]` and")
    md.append("`[this+0x78]`, calls virtuals at vtable `+0x698/+0x6a0`, obtains world")
    md.append("positions (`movsd`/`movss` triples), then calls into the item transfer")
    md.append("path. Full body: `out/loot_disasm_item_move_full.txt`.\n")
    md.append("Xrefs to `0x1834DB0` (see `out/loot_item_move_refs.txt`): 13 direct")
    md.append("calls from `0x182xxxx`, `0x183Axxx`, `0x1848xxx` (ItemIcon area) and")
    md.append("`0x456xxxx`/`0x457xxxx` (inventory UI), plus OnClicked at `0x463DD32`.")
    md.append("The code pointer also appears once in the .data code-registration")
    md.append("table at `0x10EAA510`, confirming it is a real registered method.\n")

    md.append("## Fix applied in the source\n")
    md.append("- `Data/Generation.h`: added `LootAllButton_OnClicked=0x463DB40`,")
    md.append("  `LootAllButton_Awake=0x463DDD0`, `LootAllButton_inventoryGrid=0x28`,")
    md.append("  `PlayerLoot_entitySource=0x28`.")
    md.append("- `Functions/Hooks/Hook.h`: `FindClassOwningMethodPtr` resolves the class")
    md.append("  from the verified method pointer, no names involved; `Awake` also")
    md.append("  falls back to its RVA.")
    md.append("- `Interact.h`: same class/Awake fallbacks, scan never latches out and")
    md.append("  runs at 400 ms while a panel is open (3 s idle heartbeat after the")
    md.append("  first 20 tries), `onClicked` falls back to `GameAssembly + 0x463DB40`,")
    md.append("  and grid/entity offsets now use the named constants.\n")
    md.append("## How to verify on the next run\n")
    md.append("Enable Instant Loot, open a container, and expect these new lines in")
    md.append("`log.txt` (in order):\n")
    md.append("1. `[LOOT] resolve: ... OnClicked=0x...463DB40 ...`")
    md.append("2. `[LOOT] LootAllButton class recovered by OnClicked RVA -> klass=0x...`")
    md.append("   (only if the name lookup failed)")
    md.append("3. `[LOOT] rediscover: ... btn=0x... open=1` while the panel is open")
    md.append("4. `[LOOT] open: ... btn=0x... grid=0x...`")
    md.append("5. `[LOOT] fire: path=OnClicked fast=1 btn=0x... grid=0x...`\n")
    md.append("If step 2 never logs but the name lookup works, `[HOOK] LootAllButton`")
    md.append("and the Awake hook (if the class implements Awake) cache the instance")
    md.append("directly and step 3 is not needed.")
    md.append("\n## Artifacts\n")
    for n, why in (
        ("loot_offsets.json", "confirmed fields / RVAs and their evidence"),
        ("loot_disasm_OnClicked.txt", "full LootAllButton::OnClicked body"),
        ("loot_disasm_LootAllButton_Awake.txt", "Awake (builds the [this+0x20] delegate)"),
        ("loot_disasm_LootAllButton_ctor.txt", "LootAllButton .ctor"),
        ("loot_disasm_PlayerLoot_ctor.txt", "PlayerLoot .ctor"),
        ("loot_disasm_item_move_full.txt", "full per-item move routine blob"),
        ("loot_disasm_item_move_1834DB0.txt", "first .pdata chunk (context only)"),
        ("loot_disasm_TryToMove_closure_185C650.txt", "ItemIcon.<TryToMove>b__0 closure"),
        ("loot_item_move_refs.txt", "all xrefs to the per-item move routine"),
        ("loot_method_table.txt", ".data region around OnClicked's code pointer"),
        ("playerloot_field_access.txt", "exploratory PlayerLoot field-access list"),
    ):
        md.append("- `%s` - %s" % (n, why))

    with open(os.path.join(OUT, "loot_report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print("wrote:")
    for n in sorted(os.listdir(OUT)):
        p = os.path.join(OUT, n)
        print("  %-34s %d bytes" % (n, os.path.getsize(p)))


if __name__ == "__main__":
    main()
