# Instant Loot - reverse report (Rust 26140533)

Source: `C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll`

ImageBase: 0x180000000  size 304039424


## Confirmed layout

| symbol | value | evidence |
|---|---|---|
| PlayerInventory.loot | 0x48 | PlayerLoot |
| PlayerLoot.entitySource | 0x28 | BaseEntity |
| LootAllButton.inventoryGrid | 0x28 | Rust.UI.InventoryGrid |
| LootAllButton.OnClicked | 0x463DB40 | disassembly |
| LootAllButton.Awake | 0x463DDD0 | plaintext name; builds the [this+0x20] predicate |
| LootAllButton..ctor | 0x9CB140 | disassembly |
| ItemIcon.TryToMove (parent, unconfirmed name) | 0x1834DB0 | called by OnClicked per grid item; blob 0x1834DB0..0x1835308 |
| ItemIcon.<TryToMove>b__0 closure | 0x185C650 | from the original dump |

## Why the current Instant Loot is dead

`[LOOT] poll` in the runtime log shows, on all 11 heartbeats:

```
loot=0x115F12FD960 ent=0x0 session=0x0 btn=0x0
onClicked=0x7FF967CFDB40   (= module base + 0x463DB40)
```
So `OnClicked` **was** resolved, and the code pointer is right. The
failure is the class/instance path, not the method:

1. At injection `LootAllButton` and `OnClicked` resolved (hence the
   correct RVA in every poll).
2. Afterwards the lazy resolver in `Interact.h` uses its own static
   and asks for the class again. On this build EAC clobbers metadata
   names after injection, so that later lookup can return 0. Once it
   does, `s_lootAllKlass` stays 0 for the rest of the session.
3. The instance scan is gated on `s_lootAllKlass`, so a 0 there means
   the scan never runs at all. The log contains no `[LOOT] awake:`
   and no `[LOOT] rediscover:` lines, i.e. neither the Awake hook nor
   the scene scan ever produced an instance.
4. `lootBtn` therefore stayed 0 and
   `canButton = lootSession && lootBtn && onClicked && gridOk` could
   never be true, so the game's own loot-all was never invoked.

The old code also had a one-shot class latch in `Hook.h`, a hard
1000-try latch on the scan, a 10 s idle scan interval and a trigger
gated on `entitySource`. Any one of those turns a single transient
resolution miss into a dead feature for the whole session. That is
exactly the symptom here.

`ent=0x0` is consistent with the panel being closed at the poll
instants; it is not the primary failure. The offsets are correct:
- `OnClicked` reads the grid at `this+0x28` (`0x463DBA6`).
- It calls the per-item move routine at `0x1834DB0` (`0x463DD32`).
- metadata confirms `LootAllButton` field #1 is `inventoryGrid` and
  `PlayerLoot` field #0 is `entitySource` (`revers/dump_fields.py`).

## OnClicked internals (verified)

`LootAllButton::OnClicked` RVA `0x463DB40`, body `0x463DB40..0x463DDC2`:

1. `0x463DBA6  mov rbx, [rsi+0x28]` - load `this.inventoryGrid`;
   `0x463DBAD je 0x463DDBC` - null grid raises the game's NRE.
2. Builds the grid enumerator (`call 0x869FA0`, `call 0x7E0E0`) and loops.
3. For each element resolves a virtual/interface call through the
   klass vtable (`[klass+0x12e]` count, `[klass+0xb0]` slots, `+0x138`).
4. `0x463DCFB  mov rdx, [rax+0x160]` - reads the item component; skip if 0.
5. `0x463DD0B  cmp qword [rsi+0x20], 0` - optional button-side predicate;
   when set it must return true (`call [r9+0x18]`).
6. `0x463DD32  call 0x1834DB0` with `rcx=item`, `dl=1` - move this item.

`0x1834DB0` is a shared UI move routine (contiguous COMDAT blob
`0x1834DB0..0x1835308`; `.pdata` splits it into 5 entries, so a naive
enclosing-function lookup truncates it). It reads `[this+0x160]` and
`[this+0x78]`, calls virtuals at vtable `+0x698/+0x6a0`, obtains world
positions (`movsd`/`movss` triples), then calls into the item transfer
path. Full body: `out/loot_disasm_item_move_full.txt`.

Xrefs to `0x1834DB0` (see `out/loot_item_move_refs.txt`): 13 direct
calls from `0x182xxxx`, `0x183Axxx`, `0x1848xxx` (ItemIcon area) and
`0x456xxxx`/`0x457xxxx` (inventory UI), plus OnClicked at `0x463DD32`.
The code pointer also appears once in the .data code-registration
table at `0x10EAA510`, confirming it is a real registered method.

## Fix applied in the source

- `Data/Generation.h`: added `LootAllButton_OnClicked=0x463DB40`,
  `LootAllButton_Awake=0x463DDD0`, `LootAllButton_inventoryGrid=0x28`,
  `PlayerLoot_entitySource=0x28`.
- `Functions/Hooks/Hook.h`: `FindClassOwningMethodPtr` resolves the class
  from the verified method pointer, no names involved; `Awake` also
  falls back to its RVA.
- `Interact.h`: same class/Awake fallbacks, scan never latches out and
  runs at 400 ms while a panel is open (3 s idle heartbeat after the
  first 20 tries), `onClicked` falls back to `GameAssembly + 0x463DB40`,
  and grid/entity offsets now use the named constants.

## How to verify on the next run

Enable Instant Loot, open a container, and expect these new lines in
`log.txt` (in order):

1. `[LOOT] resolve: ... OnClicked=0x...463DB40 ...`
2. `[LOOT] LootAllButton class recovered by OnClicked RVA -> klass=0x...`
   (only if the name lookup failed)
3. `[LOOT] rediscover: ... btn=0x... open=1` while the panel is open
4. `[LOOT] open: ... btn=0x... grid=0x...`
5. `[LOOT] fire: path=OnClicked fast=1 btn=0x... grid=0x...`

If step 2 never logs but the name lookup works, `[HOOK] LootAllButton`
and the Awake hook (if the class implements Awake) cache the instance
directly and step 3 is not needed.

## Artifacts

- `loot_offsets.json` - confirmed fields / RVAs and their evidence
- `loot_disasm_OnClicked.txt` - full LootAllButton::OnClicked body
- `loot_disasm_LootAllButton_Awake.txt` - Awake (builds the [this+0x20] delegate)
- `loot_disasm_LootAllButton_ctor.txt` - LootAllButton .ctor
- `loot_disasm_PlayerLoot_ctor.txt` - PlayerLoot .ctor
- `loot_disasm_item_move_full.txt` - full per-item move routine blob
- `loot_disasm_item_move_1834DB0.txt` - first .pdata chunk (context only)
- `loot_disasm_TryToMove_closure_185C650.txt` - ItemIcon.<TryToMove>b__0 closure
- `loot_item_move_refs.txt` - all xrefs to the per-item move routine
- `loot_method_table.txt` - .data region around OnClicked's code pointer
- `playerloot_field_access.txt` - exploratory PlayerLoot field-access list