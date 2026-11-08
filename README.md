# Rust-Offset-Dumper

Injected x64 C++ dumper for Rust (IL2CPP). It reads the **live** runtime through
GameAssembly exports, so it does not depend on metadata v39 being parseable
offline.

## Build

Open `Rust-Offset-Dumper.sln` in Visual Studio 2022 and build `Release | x64`.

Output:

```
bin\Release\Rust-Offset-Dumper.dll
```

## Inject

Inject `Rust-Offset-Dumper.dll` into `RustClient.exe` after the game is in the main menu
or in-game. The worker waits for IL2CPP, waits ~4 s for the scene, then dumps.

- `F8` in-game = re-dump
- `END` = stop the worker thread (DLL stays loaded)
- exported `RustOffsetDumper_Run()` = request a re-dump from your injector
- exported `RustOffsetDumper_OutputDir()` = returns the dump folder path

## Output

On inject the DLL allocates a **console window** titled
`Rust-Offset-Dumper - live IL2CPP dump` and streams every step there live (same lines
go to `Rust-Offset-Dumper_log.txt`, flushed after every line). Closing the console does
not kill the game.

Everything is written to:

```
%USERPROFILE%\Desktop\Rust-Offset-DumperDumps\
```

| File | Contents |
|---|---|
| `Rust-Offset-Dumper_log.txt` | progress, errors, timings |
| `Rust-Offset-Dumper_offsets.h` | generated offset header, all classes/fields |
| `Rust-Offset-Dumper_resolved.h` | **verified** typeinfo RVAs, static-block source, proven entity chain and ClassScan candidates |
| `Rust-Offset-Dumper_typeinfos.txt` | class -> TypeInfo RVA candidates found by scanning GameAssembly data sections |
| `Rust-Offset-Dumper_classes.txt` | full field/method layout for target classes, with code RVAs |
| `Rust-Offset-Dumper_keywords.txt` | every field whose name matches health/hp/inventory/decrypt/body/capsule/etc. |
| `Rust-Offset-Dumper_entity_chain.txt` | live BaseNetworkable static -> realm/list probe, both decryptors |
| `Rust-Offset-Dumper_camera.txt` | live `UnityEngine.Camera` matrices at native +0xB0/+0x130/+0x2FC/+0x30C |
| `Rust-Offset-Dumper_entities.txt` | live BasePlayer / BaseCombatEntity / DroppedItemContainer field values |
| `Rust-Offset-Dumper_hash_names.txt` | persistent `%hash -> Name` table. The dump seeds it and lists every unresolved hash with the slot it was seen in; fill a name in, re-run, and it is applied to class/field/type names |

## Obfuscated names (`%<40 hex>`)

Rust's metadata obfuscator replaces some identifiers with a 40-hex token. It is
a **keyed one-way hash**, not encryption: tested against 1.25M unique strings
from `GameAssembly.dll` + `global-metadata.dat` and against every plausible
textual form of two confirmed identifiers (namespace/assembly prefixes,
`get_`/`m_`, UTF-8/16/32, sha1/ripemd160/blake2b/sha2/sha3) - zero matches.
There is no reverse function and no dictionary that cracks it.

The only way to get the name back is a recorded mapping:

1. Built-in seeds: `src/generated/NameOverrides.generated.h` (38 class names and
   5 field names from the 26140533 reference build). They are applied
   automatically during every dump to class names, field names and nested type
   names (`%hash.Phrase`).
2. Unresolved fields are still dumped, but with a stable offset-based id:
   `field_0x7F0   [%ff669b2c...]` - so the layout stays usable and the hash is
   not lost.
3. `Rust-Offset-Dumper_hash_names.txt`: created in the output directory on every run.
   It contains all known pairs plus a commented template line for each hash the
   dump could not name, e.g.
   `%5231706174bf1fcab288bc4e9fec3ebdf44552d7 = ; # field Item+0x30`.
   Write the name after `=`, re-run, and the dumper resolves that hash
   everywhere: class names, field names and nested type names (`%hash.Phrase`).

Slots are never moved by this: a name is only applied to a hash that the live
metadata really produced.

## Log tags

Every line carries `[hh:mm:ss.mmm][Tthread][elapsed ms]`. The tags are:

| Tag | Meaning |
|---|---|
| `[EXPORTS]` | one line per GameAssembly export: absolute address, `+RVA`, and whether the address is a shared/ICF-folded body (tiny getters such as `image_get_name` legitimately share code) |
| `[ENUM]` | domain / thread-attach / assembly-array results, plus the final skipped/fault counters |
| `[ASM]` | per assembly: image pointer, declared class count, kept classes, targets, unnamed/duplicate/unreadable counts and timing |
| `[CLASS]` | one line per target class: klass pointer, parent, static block, and the keyword that selected it |
| `[CLASS][!]` | per-class problem: field/method walk fault, implausible offset, missing parent/static block, guard truncation |
| `[LAYOUT]` | full field layout with offsets, static/instance flags and resolved type names |
| `[SCAN]` | PE sections, bytes scanned, hit count, candidate distribution, per-section timing |
| `[TYPEINFO]` | klass -> candidate TypeInfo RVA (or `[TYPEINFO][MISS]`) |
| `[RESOLVE]` / `[SWEEP]` / `[CHAINSCAN]` | verification layer: accepted/rejected slots with the reason, static-block source, decrypted chain candidates |
| `[CAM]` / `[LIVE]` / `[CHAIN]` | live probes, including why `FindObjectsOfType` refused a type |
| `[SUMMARY]` | per-stage timings, totals and process working set |
| `[HASH]` | hash table load result and how many hashed tokens were resolved / left unresolved |

Every failure path logs the exact reason instead of silently returning, so a
dump that produces nothing still tells you which accessor or export failed.

## How it resolves things

1. `il2cpp_domain_get_assemblies` -> every assembly -> every class.
2. `il2cpp_class_get_fields` / `il2cpp_field_get_offset` for the real field layout.
3. TypeInfo RVA = any qword in a non-executable PE section that exactly equals
   the live `Il2CppClass*` (same thing the cheat's build-check does).
4. Live objects via `UnityEngine.Object.FindObjectsByType` through
   `il2cpp_runtime_invoke` (the route that works on this obfuscated build).
5. Entity chain / decryptor results are printed as measured values, not guesses.

### Verified resolution (`src/Resolver.h`)

Ported from the Vlone Rust Internal source (its `Decryptors.h`, `ChainScan.h`
and `ClassScan.h`), because a dump full of unverified numbers is worthless the
moment the build moves.

1. **TypeInfo slots** - a candidate RVA is only accepted when
   `slot(GameAssembly + rva) == klass` *and* `klass+0x10` points at a printable
   name. Slots EAC garbage-filled are dropped instead of being written out.
2. **Static blocks** - resolved in three steps: the
   `il2cpp_class_get_static_field_data` export, then `klass+0xB8`
   (`Il2CppClass::static_fields`), then the protection wrapper
   (`klass+0x28 -> klass`, then `wrapper+0xB8`). The winning path is recorded
   per class.
3. **Entity chain** - no hardcoded realm offset. Every static slot from `0x08`
   to `0x80` is decrypted with both runtime decryptors and the result is judged
   by shape (`List<T>` / `Il2CppArray`), population and whether the elements are
   real managed objects of one class. Only a chain that survives is written.
4. **Static collection sweep** - if the chain cannot be proven, every class'
   static block is walked and the biggest collection passing the same shape test
   is kept (Vlone's `ClassScan`), with a 20 s budget so it cannot stall the dump.

`Rust-Offset-Dumper_resolved.h` is the output: `verified` is `false` rather than a
fabricated number when a slot could not be checked.

## Static reversing pipeline (`tools/`)

The decryptor chains are **not typed in by hand** anymore. `tools/reverse.py`
parses `GameAssembly.dll`, takes exact function bounds from `.pdata`, symbolically
executes every 32-bit cipher block and matches the result against the known
decryptor table.

```
py tools/reverse.py              # verify + regenerate src/generated/Decryptors.generated.h
py tools/reverse.py --known-only # skip the full cipher census (fast)
```

For each routine the generator stores the function RVA, the cipher-block RVA and
a FNV-1a hash of the first 64 bytes of the block. On every dump the DLL calls
`VerifyGeneratedDecryptors()` and logs `[DECRYPT] ... ALL VERIFIED` or a per-entry
`[!!!]` mismatch. A Facepunch update therefore fails loudly instead of silently
decrypting garbage:

```
[DECRYPT] generated chains vs live GameAssembly: ALL VERIFIED
  [ OK ] EntityListDecrypt  block 0x1C5C5C0 hash 0x5974A924
  ...
```

Current result on build `26140533`: 7 chains match the binary directly, 2
(`PlayerWalkMovementBody`, `BasePlayerCapsuleCollider`) are the inverse of the
matching encryptor - both directions are equivalent, and the generated header
always carries the decrypt direction. `tools/out/decryptors.txt` is the full
report (binary chain vs header chain for every routine).

After a live dump, `tools/analyze_dump.py` turns the dumped offsets into
compile-time data:

```
py tools/analyze_dump.py                       # default: %USERPROFILE%\Desktop\Rust-Offset-DumperDumps
py tools/analyze_dump.py <dumpdir>
  -> src/generated/Offsets.generated.h  (regular gameplay offsets + verified TypeInfo RVAs)
  -> tools/out/offsets_report.md / offsets.json
```

### Static offset tables inside the DLL (`src/StaticResolver.h`)

`revers/rev_binary.py` proves every offset against `GameAssembly.dll` alone.
The DLL now does the same thing at inject time, without capstone and without
metadata parsing:

| step | what it does |
|---|---|
| anchors | every dumped field whose metadata name is readable and whose live offset is plausible |
| search | scans the mapped, non-executable PE sections for the int32 `fieldOffsets` array whose anchored entries equal those live offsets, entry by entry |
| verify | the table is accepted only when **all** anchors match; the RVA is logged per class (`[STATIC]`) |
| recover | a hidden (`%hash`) slot that the live accessor could not offset is filled from that table (poison `0x67676767` stays a hole) |

The table is a verification/fallback layer, never a source of a guessed value.
Measured on build `26140533`, the anchor search pins exactly the arrays from
`revers/DUMPER.md`:

```
Projectile    0xEC2ED00   35/35 anchors
AttackEntity  0xEC4E6D0   22/22 anchors
BasePlayer    0xEBF44B0    3/3  anchors
PlayerModel   0xEC1BD00  102/102 anchors
```

`tools/import_binary_offsets.py` turns `revers/out/binary_provenance.json` into
`src/generated/ReversOffsets.generated.h`. It is a **name source only**: a slot
whose metadata name is a one-way EAC hash gets the name that `rev_binary.py`
proved for that exact `(class, offset)`; the written offset still comes from the
live runtime or the verified table. Run it after every `rev_binary.py` run:

```
py revers\rev_binary.py
py tools\import_binary_offsets.py
```

`Rust-Offset-Dumper_offsets.h` exports only named slots: a field keeps its live name, a
community name, or the name that `rev_binary.py` proved for that exact slot. A
slot that is still an EAC hash after all three is omitted, so the header never
contains `field_0xNNN` placeholders. `tools/compare_revers.py` reports
`OK / MISSING / MISMATCH` for all 207 proof fields after the next dump +
`analyze_dump.py`:

```
py tools\compare_revers.py
```

The DLL now walks **only** the curated class set (`IsDumpClass` in
`Dumper.h`) and skips method tables (`kDumpMethods = false`), because on this
build every class/method name goes through a protected trampoline. That turns a
30+ minute enumeration into seconds while keeping every offset that the regular
header needs. All fields of those classes are exported, not only
health/inventory keywords.

`Il2Cpp.h` picks the header up automatically via `__has_include`, so a re-dump +
re-run + rebuild is the whole loop.

To cross-check a third-party offsets header (for example the Discord header for
build 26140533) against what the dumper actually measured:

```
py tools/check_reference.py path\to\reference_offsets.hpp
```

It reports `CONFIRMED` / `OFFSET-ONLY` / `MISSING` per field and validates
TypeInfo RVAs. `tools/verify_live.py` does the same for TypeInfo slots directly
against a running client, without a dump:

```
py tools/verify_live.py [--pid 7640]
```

Every decryptor chain also exists as many inlined copies in the image (e.g.
`ClientEntities` has 387); the generated header pins one verified copy and the
FNV hash proves the build, while `tools/dbg_copies.py` lists them all if a
reference uses a different copy address.

`tools/recon.py` prints the PE section map / export count, and
`tools/metadata_probe.py` documents why offline metadata parsing is not an
option: `global-metadata.dat` has a valid v39 header but the section table and
strings are encrypted.

## Notes

- `class_get_fields`, `field_get_offset`, `field_get_flags`, and
  `field_static_get_value` are wrapped in SEH guards, so one protected class
  cannot take the game down during the full enumeration.
- The generated header keeps original field names in comments. Obfuscated `%`
  class names are sanitized into valid C++ identifiers.
- If a class is not a `UnityEngine.Object`, `FindObjectsByType` refuses it --
  that failure is printed instead of being hidden.
