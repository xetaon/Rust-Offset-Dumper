# DUMPER.md — dump-free offset extraction (Rust build 26140533)

This document records the exact **static** pipeline that produced the valid
field offsets for `BasePlayer`, `Projectile`, `AttackEntity` and `PlayerModel`
from `GameAssembly.dll` only. No live dump, no process injection and no
`tools/reference` table is a source of any offset.

- Target: `C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll`
- Build id: `26140533`
- Size: `304,039,424` bytes, image base `0x180000000`
- Metadata: `RustClient_Data\il2cpp_data\Metadata\global-metadata.dat` (v39)
- Interpreter: `py -3` (Python 3.15, capstone 5.x)
- All scripts live in this folder: `C:\Users\SystemX\Desktop\Rust-Offset-Dumper\revers`

> The old evidence-join scripts (`rev_baseplayer.py`, `rev_classes.py`) are kept
> only as the origin of the *requested field list / validation keys*. They are
> **not** an offset source in the current pipeline.

---

## 1. Result

`py -3 revers\rev_binary.py` currently produces:

| class | requested | from `.rdata` table | from code `[this+disp]` | missing |
|---|---:|---:|---:|---:|
| BasePlayer  | 24  | 0   | 24  | 0 |
| Projectile  | 55  | 46  | 9   | 0 |
| AttackEntity| 22  | 22  | 0   | 0 |
| PlayerModel | 106 | 0   | 106 | 0 |

Artifacts written to `revers/out/`:

- `BasePlayer_binary.h`, `Projectile_binary.h`, `AttackEntity_binary.h`,
  `PlayerModel_binary.h` — ready-to-use C++ constants.
- `binary_provenance.json` — per-field evidence (table RVA + index, or the
  exact instruction / method RVA / instruction RVA).
- `binary_report.md` — the same evidence in Markdown tables.

The emitted values were also checked against the requested list: **207/207
match, 0 missing, 0 wrong**.

---

## 2. Why the earlier addresses were wrong

The previous notes mixed **file offsets** with **RVAs**. For `.rdata`:

```
RVA = file_offset + 0x2200
```

so e.g. the Projectile table at file offset `0xEC2CB00` is RVA `0xEC2ED00`.
The old `Il2CppType` / sizes RVAs were the same kind of mistake. The correct,
verified addresses for this DLL are:

| artefact | RVA |
|---|---|
| `Il2CppType` pointer table | `0xFBABD30` |
| `Il2CppTypeDefinitionSizes` pointer table | `0x110F1B00` |
| BasePlayer field-offset table | not located (few non-hidden runs; code covers all fields) |
| Projectile field-offset table | `0xEC2ED00` (raw `0xEC2CB00`) |
| AttackEntity field-offset table | `0xEC4E6D0` (raw `0xEC4C4D0`) |
| PlayerModel field-offset table | not located (few non-hidden runs; code covers all fields) |

At `0xFBABD30`: index `43666` → `BasePlayer`, `57697` → `Projectile`,
`43210` → `AttackEntity`, `57203` → `PlayerModel`, `64994` → `Vector3`,
`60175` → `System.Single`.
At `0x110F1B00`: BasePlayer `0x7F8`, Projectile `0x200`,
AttackEntity `0x388`, PlayerModel `0x6E0`, Vector3 `(28, 12)`.

### How the correct tables were found

1. Metadata (`tools/meta_rva.py`) gives each type definition a `byval_type`
   index into the `Il2CppType` table. For `BasePlayer` the type struct with
   `data == 5604, type == 0x12` was located in `.data`, then every qword
   pointer to it was searched. The candidate **base = pointer_position − 43666*8**
   was validated against ~800 other type definitions — only `0xFBABD30` maps
   every sampled `byval_type` back to its own type definition.
2. The sizes table was found from the unique
   `{0x7F8, -1, 0, 0}` (`BasePlayer` instance size) structure at
   `0xECDB580`, then its pointer back-reference gave base `0x110F1B00`.
   Validation: for value types `native_size == instance_size − 0x10`
   (Vector3 `28/12`, Quaternion `32/16`, MinMax `24/8`, TurnSegment `32/16`).
3. The per-class field-offset tables are arrays of `int32`, **one entry per
   metadata field in declaration order**, including hidden/static entries.
   `0x67676767` means “offset not stored in this table” (174,320 occurrences,
   all inside `.rdata`, never referenced by code).
4. A table is verified structurally: for every run of consecutive *named*
   metadata fields, the difference between two table entries must equal the
   difference computed from the declared field types (alignment + type size).
   Example: AttackEntity scores **21/21** relations; Projectile **34/34**.

---

## 3. Which script did what

### Main pipeline

| File | Role |
|---|---|
| `rev_binary.py` | **The only thing needed for the final offsets.** Loads PE + v39 metadata, verifies/relocates the `Il2CppType` and sizes tables, locates each class's `.rdata` field-offset table by layout matching, disassembles all of the class's IL2CPP methods with capstone and collects real `[this+disp]` operands (stack registers excluded). Writes the four headers, provenance JSON and report. |
| `locate_tables_current.py` | Reproduces the `Il2CppType` table discovery from metadata `byval_type` → `data == type-def` cross-check. Prints the correct `0xFBABD30` base. |
| `locate_sizes_current.py` | Reproduces `Il2CppTypeDefinitionSizes` discovery from the unique `0x7F8` struct and back-references. Prints `0x110F1B00`. |
| `tools/meta_rva.py` | Offline v39 metadata reader + PE/RVA mapper + method-token → native RVA resolver. The backbone of every script here. |

### Evidence / exploration scripts that led to the result

| File | What it proved |
|---|---|
| `dump_fields.py` | Dumps field names/order/tokens for any type through the v39 reader; used to confirm `Projectile`, `BasePlayer`, `AttackEntity`, `PlayerModel` field order. |
| `probe_fieldoffsets.py` | First look at the `Il2CppTypeDefinitionSizes` table (`0x7F8`, `0x200`, `0x388`, `0x6E0`). |
| `cmp_layout.py` | Compares metadata layout against the `.rdata` offset tables; exposed the hidden-field/poison mismatch and the need for segment-based table matching. |
| `proto_layout.py`, `proto_layout2.py`, `proto_layout3.py` | Layout experiments: parent-chain resolution, generic parents (`ListComponent\`1` → `Il2CppGenericClass`), value-type size = `instance_size − 0x10`. |
| `find_seq.py`, `find_seq2.py` | Raw search for absolute offset sequences (`0x2F0,0x2F4,…`) in `.rdata`; located the true Projectile and AttackEntity tables. |
| `mask_scan.py` | Tested a poison-mask hypothesis; disproved it (hidden fields are not always poison) and confirmed table length = metadata field count. |
| `coverage_code.py` | Code-displacement coverage check: Projectile 55/55, PlayerModel 106/106, BasePlayer 24/24, AttackEntity 14/22 (the 8 gaps were then closed by the AttackEntity table). |
| `disasm_proj.py` | Early capstone scan of `Projectile` methods; established that `[this+disp]` operands are reliable evidence. |
| `find_poison_code.py` | Proved `0x67676767` never appears in executable sections. |
| `find_il2cpptype_struct.py` | Found `Il2CppType` structs by scanning for the type-def `data` qword; basis for the final table search. |
| `scan_ptr_runs.py`, `scan_type_ptr_runs.py` | Located long qword pointer runs in `.rdata`/`.data` (types, sizes and method-pointer tables). |
| `probe_arrays.py`, `probe_types.py`, `find_lea_refs.py`, `find_lea_refs.py` | Array/type/LEA probes that ruled out wrong candidate tables. |
| `probe_req_tables.py` | Confirms the final request offsets are present in the verified `.rdata` tables. |
| `rva_check.py`, `pe.py`, `scan_sections.py` | PE/section sanity checks that exposed the RVA-vs-file-offset error. |

### Legacy (validation / history only — never an offset source)

| File | Role |
|---|---|
| `rev_baseplayer.py` | Historical live/community evidence join for BasePlayer; now used only as the source of the requested field names. |
| `rev_classes.py` | Same for Projectile / AttackEntity / PlayerModel request lists. |
| `rev_loot.py`, `rev_lifecycle.py`, `rev_item_move_full.py`, `find_item_move_refs.py`, `find_loot_method_table.py`, `rev_playerloot_fields.py`, `gen_loot_artifacts.py` | Earlier Instant-Loot RE (different feature). |
| everything else | Small probes collected during the reverse sessions. They are all kept here on request; they are not part of `rev_binary.py`. |

---

## 4. Reproduction

```
cd C:\Users\SystemX\Desktop\Rust-Offset-Dumper
py -3 revers\rev_binary.py
```

Expected output:

```
[+] BasePlayer     table=0   code=24  missing=0
[+] Projectile     table=46  code=9   missing=0
[+] AttackEntity   table=22  code=0   missing=0
[+] PlayerModel    table=0   code=106 missing=0
[+] types table 0xFBABD30  sizes table 0x110F1B00
```

Exit code is `0` only when every requested field has binary evidence.

To verify the supporting tables first:

```
py -3 revers\locate_tables_current.py
py -3 revers\locate_sizes_current.py
```

---

## 5. Evidence rules used by `rev_binary.py`

A field offset is accepted only if at least one of these is true:

1. It occurs in the class's **verified `.rdata` field-offset table**. The table
   itself is accepted only when the layout relations of its named-field runs
   match the metadata-derived layout (≥ 50 % of all relations, and in practice
   `21/21` and `34/34`).
2. It occurs as a real memory operand `[reg + disp]` in one of the class's own
   IL2CPP methods. `rsp`/`rbp`-relative operands are rejected (they are stack
   slots, not fields). The exact instruction and method RVA are recorded in
   `binary_provenance.json`.

Nothing is inferred from the live game, from `Offsets.generated.h`, or from a
community/reference offset table. The requested list is used only as a lookup
key; every written value is independently present in the binary at the
reported table index or instruction.

---

## 6. Known limitations

- `BasePlayer` and `PlayerModel` field-offset tables are not stored in this
  build (their tables are hidden/generated); their offsets come entirely from
  code operands.
- A code operand proves that the class touches `this+offset`; pairing it with a
  field *name* is only exact for non-hidden metadata names. Hidden fields are
  keyed by the requested offset and validated by the table where available.
- Offsets are tied to build `26140533`. A game update changes the DLL, the
  metadata and the tables; re-run the pipeline against the new DLL.
