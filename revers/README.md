# Rust 26140533 - Instant Loot reverse

Everything here is static analysis of the local
`C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll`
(build `26140533`, image base `0x180000000`). No game process and no cheat
build is required.

Python: use `py -3` (the `python` WindowsApps alias is a broken stub).
Requires `capstone` (5.x).

## Dump-free offset pipeline (current)

`rev_binary.py` derives/verifies every requested offset from
`GameAssembly.dll` alone — no RustClient process, no live dump, no reference
table:

```
py -3 revers\rev_binary.py
```

Outputs live in `out/`: `*_binary.h`, `binary_provenance.json`,
`binary_report.md`. See `DUMPER.md` for the full evidence chain, the correct
table RVAs (`Il2CppType = 0xFBABD30`, sizes = `0x110F1B00`,
Projectile offsets = `0xEC2ED00`, AttackEntity = `0xEC4E6D0`), and the
description of every helper script in this folder.

## Legacy Instant-Loot scripts

| Script | What it does |
|---|---|
| `rev_loot.py` | Minimal PE / `.pdata` parser shared by the rest. Prints PE facts and disassembles around `LootAllButton::OnClicked`. |
| `rev_trymove.py`, `rev_trymove2.py` | Early probes for the ItemIcon move routine / `<TryToMove>b__0`. |
| `rev_item_move_full.py` | Dumps the **whole** per-item move routine (`0x1834DB0..0x1835308`). `.pdata` splits it into several contiguous COMDAT chunks, so a naive enclosing-function lookup truncates it. |
| `find_item_move_refs.py` | Finds every rel32 call/jmp and every absolute code-pointer reference to `0x1834DB0`. |
| `find_loot_method_table.py` | Finds the `.data` code-registration slot that holds the `OnClicked` pointer and prints the surrounding method-pointer table. |
| `dump_fields.py` | Dumps il2cpp field definitions (names/order/tokens) via `tools/meta_rva.py`'s v39 reader. Confirms `LootAllButton.inventoryGrid` and `PlayerLoot.entitySource`. |
| `rev_lifecycle.py` | Disassembles `LootAllButton::Awake` / `.ctor` and `PlayerLoot::.ctor` - the places that reveal which offsets the declared fields live at. |
| `rev_playerloot_fields.py` | Exploratory scan of all `PlayerLoot` methods for `this+0x20..0x38` accesses (noisy; kept for reference). |
| `gen_loot_artifacts.py` | Writes `out/loot_offsets.json` and `out/loot_report.md`; also emits the OnClicked / closure / first-chunk disassemblies. |

Suggested order:

```
py -3 revers\rev_item_move_full.py
py -3 revers\find_item_move_refs.py
py -3 revers\find_loot_method_table.py
py -3 revers\dump_fields.py LootAllButton PlayerLoot PlayerInventory
py -3 revers\rev_lifecycle.py
py -3 revers\gen_loot_artifacts.py
```

## Key results

* `PlayerInventory.loot          = +0x48`  (PlayerLoot component)
* `PlayerLoot.entitySource       = +0x28`  (panel-open flag, declared field #0)
* `LootAllButton.inventoryGrid   = +0x28`  (declared field #1)
* `LootAllButton` declared field #0 is hashed and lives at `+0x20`; `Awake`
  builds the predicate/delegate that `OnClicked` tests via `[this+0x20]`.
* `LootAllButton` has only 3 methods: `OnClicked`, `.ctor`, `Awake`
  - `OnClicked = RVA 0x463DB40` (token `0x0602a4dc`)
  - `.ctor     = RVA 0x009CB140`
  - `Awake     = RVA 0x463DDD0` (token `0x0602a4de`, plaintext name)
* `OnClicked` internals:
  - `0x463DBA6  mov rbx, [rsi+0x28]`  -> inventoryGrid
  - `0x463DD32  call 0x1834DB0`       -> move one item (`rcx=item`, `dl=1`)
* per-item move routine: contiguous blob `0x1834DB0..0x1835308`, registered
  in the `.data` code table at `0x10EAA510`.
* OnClicked code pointer slot in `.data`: `0x10F88868`.

The offsets were never the problem. The feature never fired because the
`LootAllButton` instance was never acquired (`btn=0` on every poll, no
`[LOOT] awake:` / `[LOOT] rediscover:` lines), while the `OnClicked` pointer
itself was already correct in the log. The old one-shot class latch, 1000-try
scan latch and 10 s idle scan made any single resolution miss permanent. See
`out/loot_report.md` for the full analysis and the source fix.

## Outputs (`out/`)

| File | Content |
|---|---|
| `loot_offsets.json` | Confirmed fields/RVAs plus evidence. |
| `loot_report.md` | Human-readable analysis, fix and verification checklist. |
| `loot_disasm_OnClicked.txt` | Full `LootAllButton::OnClicked`. |
| `loot_disasm_LootAllButton_Awake.txt` | `LootAllButton::Awake` (builds the `[this+0x20]` delegate). |
| `loot_disasm_LootAllButton_ctor.txt` | `LootAllButton::.ctor`. |
| `loot_disasm_PlayerLoot_ctor.txt` | `PlayerLoot::.ctor` (initializes field #3). |
| `loot_disasm_item_move_full.txt` | Full per-item move routine. |
| `loot_disasm_item_move_1834DB0.txt` | First `.pdata` chunk (context only). |
| `loot_disasm_TryToMove_closure_185C650.txt` | `ItemIcon.<TryToMove>b__0` closure. |
| `loot_item_move_refs.txt` | All xrefs to the per-item move routine. |
| `loot_method_table.txt` | `.data` method-pointer table around OnClicked. |
| `playerloot_field_access.txt` | Exploratory `this+0x20..0x38` access list. |
