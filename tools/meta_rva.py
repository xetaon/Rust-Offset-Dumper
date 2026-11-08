#!/usr/bin/env python3
"""
meta_rva.py - offline il2cpp metadata <-> GameAssembly.dll RVA mapper.

Target: Rust build 26140533, global-metadata version 39.

This is the offline companion to the live Rust-Offset-Dumper.  It reads
global-metadata.dat (v39 struct layouts) and GameAssembly.dll, then maps
Il2CppMethodDefinition tokens to native RVAs through the per-image method
pointer tables stored in GameAssembly's .data.

Usage
-----
  python meta_rva.py --list-images
  python meta_rva.py --type ItemIcon
  python meta_rva.py --type ItemIcon --method OnPointerEnter
  python meta_rva.py --type-index 2293
  python meta_rva.py --token 0x600e957
  python meta_rva.py --search TryToMove
  python meta_rva.py --stats

Notes
-----
* Method names for game assemblies are hashed ("%<sha1>"); Unity message
  methods (Awake/Update/OnGUI/...), .ctor and compiler-generated names
  (<Foo>b__0, <Foo>d__1, <>c__DisplayClass1_0) stay plaintext.
* Method lookup formula:
      slot = image_method_table_base + (token & 0xFFFFFF) * 8
      rva  = qword[slot] - 0x180000000
  The table base differs per image.  Verified bases are listed below; for
  other images the base is auto-detected by scanning .data.
"""

import argparse
import struct
import sys

DEFAULT_METADATA = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\RustClient_Data\il2cpp_data\Metadata\global-metadata.dat"
DEFAULT_DLL = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"

IMAGE_BASE = 0x180000000

# Verified per-image method pointer table bases (build 26140533).
KNOWN_METHOD_TABLE_BASES = {
    "Assembly-CSharp.dll": 0x10E36188,
    "Assembly-CSharp-firstpass.dll": 0x10CAAB18,
    "Facepunch.Unity.dll": 0x110AD0E8,
}

# PE section layout of GameAssembly.dll (build 26140533).  Used only when a
# proper PE parse is not available; prefer parsing the real headers.
_T_FALLBACK_SECTIONS = [
    # name, va, vsize, raw, rawsize
    (".text", 0x1000, 0x8E4400, 0x400, 0x8E4400),
    ("il2cpp", 0x8E6000, 0xE2CE600, 0x8E4800, 0xE2CE600),
    (".rdata", 0xEBB5000, 0x20C6800, 0xEBB2E00, 0x20C6800),
    (".data", 0x10C7C000, 0xA45E00, 0x10C79600, 0xA45E00),
    (".pdata", 0x119B5000, 0x82C800, 0x116BF400, 0x82C800),
]


class Pe:
    """Minimal PE image mapper (no external deps)."""

    def __init__(self, path):
        self.path = path
        with open(path, "rb") as f:
            self.data = f.read()
        d = self.data
        e_lfanew = struct.unpack_from("<I", d, 0x3C)[0]
        assert d[e_lfanew:e_lfanew + 4] == b"PE\0\0", "not a PE file"
        coff = e_lfanew + 4
        nsec = struct.unpack_from("<H", d, coff + 2)[0]
        opt_size = struct.unpack_from("<H", d, coff + 16)[0]
        opt = coff + 20
        self.image_base = struct.unpack_from("<Q", d, opt + 24)[0]
        self.section_alignment = struct.unpack_from("<I", d, opt + 32)[0]
        sec = opt + opt_size
        self.sections = []
        for i in range(nsec):
            b = sec + i * 40
            name = d[b:b + 8].split(b"\0")[0].decode("ascii", "replace")
            vsize, va, rawsize, raw = struct.unpack_from("<IIII", d, b + 8)
            self.sections.append({
                "name": name, "va": va, "vsize": vsize,
                "raw": raw, "rawsize": rawsize,
            })

    def rva_to_off(self, rva):
        for s in self.sections:
            if s["va"] <= rva < s["va"] + s["rawsize"]:
                return s["raw"] + (rva - s["va"])
        return None

    def off_to_rva(self, off):
        for s in self.sections:
            if s["raw"] <= off < s["raw"] + s["rawsize"]:
                return s["va"] + (off - s["raw"])
        return None

    def qword(self, rva):
        o = self.rva_to_off(rva)
        if o is None:
            return None
        return struct.unpack_from("<Q", self.data, o)[0]


class Metadata:
    """global-metadata.dat reader for il2cpp metadata version 39."""

    # v39 header section order (no typeInlineArrays in v39).
    SECTION_NAMES = (
        "stringLiteral stringLiteralData string events properties methods "
        "parameterDefaultValues fieldDefaultValues fieldAndParameterDefaultValueData "
        "fieldMarshaledSizes parameters fields genericParameters "
        "genericParameterConstraints genericContainers nestedTypes interfaces "
        "vtableMethods interfaceOffsets typeDefinitions images assemblies fieldRefs "
        "referencedAssemblies attributeData attributeDataRange "
        "unresolvedVirtualCallParameterTypes unresolvedVirtualCallParameterRanges "
        "windowsRuntimeTypeNames windowsRuntimeStrings exportedTypeDefinitions"
    ).split()

    def __init__(self, path):
        with open(path, "rb") as f:
            self.data = f.read()
        d = self.data
        magic, version = struct.unpack_from("<Ii", d, 0)
        assert magic == 0xFAB11BAF, "bad metadata magic %#x" % magic
        assert version == 39, "expected metadata v39, got %d" % version
        self.version = version

        self.sections = {}
        off = 8
        for name in self.SECTION_NAMES:
            o, size, count = struct.unpack_from("<iii", d, off)
            off += 12
            self.sections[name] = (o, size, count)

        # sanity checks on element sizes
        td = self.sections["typeDefinitions"]
        md = self.sections["methods"]
        self.type_size = td[1] // td[2]
        self.method_size = md[1] // md[2]
        assert self.type_size == 82, "unexpected type def size %d" % self.type_size
        assert self.method_size == 32, "unexpected method def size %d" % self.method_size

        self.type_count = td[2]
        self.method_count = md[2]

        # string heap
        self.s_off, self.s_size, _ = self.sections["string"]

        # nested type map (child -> parent), built lazily
        self._parent_of = None
        self._images = None

    # -- strings ---------------------------------------------------------
    def string(self, idx):
        if idx < 0 or idx >= self.s_size:
            return None
        start = self.s_off + idx
        end = self.data.find(b"\0", start)
        if end < 0:
            return None
        raw = self.data[start:end]
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return raw.decode("latin-1")

    # -- type definitions ------------------------------------------------
    def type(self, idx):
        b = self.sections["typeDefinitions"][0] + idx * self.type_size
        d = self.data
        name_idx, ns_idx = struct.unpack_from("<ii", d, b)
        byval, decl, parent = struct.unpack_from("<iii", d, b + 8)
        gen = struct.unpack_from("<H", d, b + 20)[0]
        flags = struct.unpack_from("<I", d, b + 22)[0]
        first_field, first_method, first_event, first_prop = struct.unpack_from("<iiii", d, b + 26)
        nested_start, iface_start, vtable_start, iface_off_start = struct.unpack_from("<iiii", d, b + 42)
        mc, pc, fc, ec, ntc, vc, ic, _ioc = struct.unpack_from("<8H", d, b + 58)
        bitfield, token = struct.unpack_from("<II", d, b + 74)
        return {
            "index": idx,
            "name": self.string(name_idx),
            "namespace": self.string(ns_idx),
            "name_index": name_idx,
            "namespace_index": ns_idx,
            "byval_type": byval,
            "declaring_type": decl,
            "parent_type": parent,
            "generic_container": gen,
            "flags": flags,
            "first_field": first_field,
            "field_count": fc,
            "first_method": first_method,
            "method_count": mc,
            "first_event": first_event,
            "event_count": ec,
            "nested_start": nested_start,
            "nested_count": ntc,
            "token": token,
        }

    # -- method definitions ----------------------------------------------
    def method(self, idx):
        b = self.sections["methods"][0] + idx * self.method_size
        d = self.data
        name_idx = struct.unpack_from("<i", d, b)[0]
        decl = struct.unpack_from("<H", d, b + 4)[0]
        ret = struct.unpack_from("<i", d, b + 6)[0]
        param_start = struct.unpack_from("<i", d, b + 14)[0]
        gen = struct.unpack_from("<H", d, b + 18)[0]
        token = struct.unpack_from("<I", d, b + 20)[0]
        flags, iflags, slot, pcnt = struct.unpack_from("<4H", d, b + 24)
        return {
            "index": idx,
            "name": self.string(name_idx),
            "name_index": name_idx,
            "declaring_type": decl,
            "return_type": ret,
            "parameter_start": param_start,
            "generic_container": gen,
            "token": token,
            "flags": flags,
            "iflag": iflags,
            "slot": slot,
            "param_count": pcnt,
        }

    def method_params(self, m):
        """Return [(name, type_index)] for a method (names are hashed for game code)."""
        off = self.sections["parameters"][0]
        out = []
        if m["parameter_start"] < 0:
            return out
        for k in range(m["param_count"]):
            b = off + (m["parameter_start"] + k) * 12
            name_idx, _tok, type_idx = struct.unpack_from("<iii", self.data, b)
            out.append((self.string(name_idx), type_idx))
        return out

    # -- images ----------------------------------------------------------
    @property
    def images(self):
        if self._images is not None:
            return self._images
        off, size, count = self.sections["images"]
        # v39 Il2CppImageDefinition is 36 bytes (nameIndex, assemblyIndex,
        # firstTypeIndex u16 + typeCount u32 packed, exported..., token)
        assert size // count == 36, "unexpected image struct size %d" % (size // count)
        out = []
        for i in range(count):
            b = off + i * 36
            name_idx, asm_idx = struct.unpack_from("<ii", self.data, b)
            first_type = struct.unpack_from("<H", self.data, b + 8)[0]
            type_count = struct.unpack_from("<I", self.data, b + 10)[0]
            token = struct.unpack_from("<I", self.data, b + 28)[0]
            out.append({
                "index": i,
                "name": self.string(name_idx),
                "assembly_index": asm_idx,
                "first_type": first_type,
                "type_count": type_count,
                "token": token,
            })
        self._images = out
        return out

    def image_of_type(self, type_index):
        for im in self.images:
            if im["first_type"] <= type_index < im["first_type"] + im["type_count"]:
                return im
        return None

    def _build_method_image_map(self):
        # methods are laid out contiguously per type; a type owns
        # [first_method, first_method + method_count).  Build a starts array
        # once so image_of_method is O(log n) instead of O(n).
        import bisect
        rows = []
        for t_idx in range(self.type_count):
            t = self.type(t_idx)
            if t["first_method"] >= 0 and t["method_count"] > 0:
                rows.append((t["first_method"], t_idx))
        rows.sort()
        self._mimg_starts = [r[0] for r in rows]
        self._mimg_type = [r[1] for r in rows]
        self._mimg_bisect = bisect

    def image_of_method(self, method_index):
        if not hasattr(self, "_mimg_starts"):
            self._build_method_image_map()
        i = self._mimg_bisect.bisect_right(self._mimg_starts, method_index) - 1
        if i < 0:
            return None
        t_idx = self._mimg_type[i]
        t = self.type(t_idx)
        if not (t["first_method"] <= method_index < t["first_method"] + t["method_count"]):
            return None
        return self.image_of_type(t_idx)

    # -- nested types ----------------------------------------------------
    @property
    def parent_of(self):
        if self._parent_of is not None:
            return self._parent_of
        n_off = self.sections["nestedTypes"][0]
        parent = {}
        for i in range(self.type_count):
            t = self.type(i)
            if t["nested_count"] and t["nested_start"] >= 0:
                for k in range(t["nested_count"]):
                    child = struct.unpack_from("<i", self.data, n_off + (t["nested_start"] + k) * 4)[0]
                    parent[child] = i
        self._parent_of = parent
        return parent

    def enclosing_type(self, type_index):
        p = self.parent_of.get(type_index)
        while p is not None and (self.type(p)["name"] or "").startswith("<"):
            p = self.parent_of.get(p)
        return p if p is not None else type_index


class RvaMapper:
    """Maps metadata tokens to GameAssembly RVAs."""

    def __init__(self, metadata, pe):
        self.meta = metadata
        self.pe = pe
        self._detected_bases = {}
        self._rva_cache = {}

    # -- code pointer validation ----------------------------------------
    def _valid_code_ptr(self, value):
        if value is None:
            return False
        rva = value - IMAGE_BASE
        if rva <= 0:
            return False
        return self.pe.rva_to_off(rva) is not None

    def _is_text_like(self, rva):
        """Reject pointers into the metadata blob region."""
        o = self.pe.rva_to_off(rva)
        if o is None:
            return False
        # first byte must not be 0x00/0xFF for a real function prologue
        return self.pe.data[o] not in (0x00, 0xFF)

    def table_base_for_image(self, image):
        name = image["name"] or ""
        if name in KNOWN_METHOD_TABLE_BASES:
            return KNOWN_METHOD_TABLE_BASES[name]
        if name in self._detected_bases:
            return self._detected_bases[name]
        base = self.detect_table_base(image)
        self._detected_bases[name] = base
        return base

    def detect_table_base(self, image):
        """Brute-force the method pointer table base for an image.

        A correct base makes the qwords at every used token index decode to
        code pointers (0x180000000 + rva) inside the PE image.
        """
        sample = []
        for t_idx in range(image["first_type"], image["first_type"] + image["type_count"]):
            t = self.meta.type(t_idx)
            for mi in range(t["first_method"], t["first_method"] + t["method_count"]):
                m = self.meta.method(mi)
                if 0 < (m["token"] & 0xFFFFFF) < 0x1000000:
                    sample.append(m["token"] & 0xFFFFFF)
        # keep a spread-out subset
        sample = sample[::max(1, len(sample) // 40)][:40]
        if not sample:
            return None

        data_sec = next((s for s in self.pe.sections if s["name"] == ".data"), None)
        if data_sec is None:
            return None
        best_base, best_score = None, -1
        for base in range(data_sec["va"], data_sec["va"] + data_sec["rawsize"], 8):
            score = 0
            for tok in sample[:12]:
                v = self.pe.qword(base + tok * 8)
                if self._valid_code_ptr(v):
                    score += 1
            if score > best_score:
                best_score, best_base = score, base
            if score == len(sample[:12]):
                break
        if best_base is not None and best_score >= max(2, len(sample[:12]) // 2):
            return best_base
        return None

    # -- token -> RVA ----------------------------------------------------
    def rva_for_method(self, method):
        key = method["index"]
        if key in self._rva_cache:
            return self._rva_cache[key]
        info = self._rva_for_method_uncached(method)
        self._rva_cache[key] = info
        return info

    def _rva_for_method_uncached(self, method):
        image = self.meta.image_of_method(method["index"])
        if image is None:
            return None
        base = self.table_base_for_image(image)
        if base is None:
            return None
        slot = base + (method["token"] & 0xFFFFFF) * 8
        value = self.pe.qword(slot)
        if value is None:
            return None
        rva = value - IMAGE_BASE
        if rva <= 0:
            return None
        return {"rva": rva, "slot": slot, "image": image["name"], "image_base": base}

    def rva_for_token(self, token):
        image = self.token_image(token)
        if image is None:
            return None
        base = self.table_base_for_image(image)
        if base is None:
            return None
        slot = base + (token & 0xFFFFFF) * 8
        value = self.pe.qword(slot)
        if value is None:
            return None
        return {"rva": value - IMAGE_BASE, "slot": slot, "image": image["name"], "image_base": base}

    def token_image(self, token):
        """Find the image that owns a method token.

        Method tokens are only unique within an image, so we prefer images we
        already know the table base for.
        """
        known = [im for im in self.meta.images if im["name"] in KNOWN_METHOD_TABLE_BASES]
        for im in known:
            base = KNOWN_METHOD_TABLE_BASES[im["name"]]
            value = self.pe.qword(base + (token & 0xFFFFFF) * 8)
            if self._valid_code_ptr(value) and self._is_text_like(value - IMAGE_BASE):
                return im
        for im in self.meta.images:
            base = self.detect_table_base(im)
            if base is None:
                continue
            value = self.pe.qword(base + (token & 0xFFFFFF) * 8)
            if self._valid_code_ptr(value) and self._is_text_like(value - IMAGE_BASE):
                return im
        return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_types(meta, needle):
    needle_l = needle.lower()
    hits = []
    for i in range(meta.type_count):
        t = meta.type(i)
        name = t["name"] or ""
        full = (t["namespace"] + "." + name) if t["namespace"] else name
        if needle_l in name.lower() or needle_l in full.lower():
            hits.append(t)
    return hits


def print_type(meta, mapper, t, only_method=None):
    ns = (t["namespace"] + ".") if t["namespace"] else ""
    print("TYPE %5d  %s%s  token=%#010x  firstMethod=%d  methods=%d  firstField=%d  fields=%d  flags=%#x"
          % (t["index"], ns, t["name"], t["token"], t["first_method"],
             t["method_count"], t["first_field"], t["field_count"], t["flags"]))
    if t["method_count"] <= 0:
        return
    for ordn in range(t["method_count"]):
        mi = t["first_method"] + ordn
        m = meta.method(mi)
        if only_method is not None and only_method.lower() not in (m["name"] or "").lower():
            continue
        info = mapper.rva_for_method(m)
        rva = info["rva"] if info else 0
        print("  ord=%3d  idx=%6d  tok=%#010x  rva=%#010x  p=%d  flags=%#06x  slot=%d  %s"
              % (ordn, mi, m["token"], rva, m["param_count"], m["flags"], m["slot"], m["name"]))


def cmd_list_images(meta, mapper):
    print("%4s %-40s %8s %10s %12s %12s" % ("idx", "name", "firstType", "typeCount", "tableBase", "methods"))
    for im in meta.images:
        base = KNOWN_METHOD_TABLE_BASES.get(im["name"] or "")
        shown = ("%#x" % base) if base else "-"
        n_methods = 0
        for t_idx in range(im["first_type"], im["first_type"] + im["type_count"]):
            n_methods += meta.type(t_idx)["method_count"]
        print("%4d %-40s %8d %10d %12s %12d"
              % (im["index"], im["name"], im["first_type"], im["type_count"], shown, n_methods))


def cmd_stats(meta, mapper):
    print("metadata version : %d" % meta.version)
    print("types            : %d" % meta.type_count)
    print("methods          : %d" % meta.method_count)
    print("images           : %d" % len(meta.images))
    hashed_types = 0
    hashed_methods = 0
    for i in range(meta.type_count):
        if (meta.type(i)["name"] or "").startswith("%"):
            hashed_types += 1
    for i in range(meta.method_count):
        if (meta.method(i)["name"] or "").startswith("%"):
            hashed_methods += 1
    print("hashed type names: %d" % hashed_types)
    print("hashed meth names: %d" % hashed_methods)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Offline il2cpp metadata -> RVA mapper (Rust build 26140533)")
    ap.add_argument("--metadata", default=DEFAULT_METADATA)
    ap.add_argument("--dll", default=DEFAULT_DLL)
    ap.add_argument("--list-images", action="store_true")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--type", help="type name (plaintext or substring)")
    ap.add_argument("--type-index", type=int, help="type definition index")
    ap.add_argument("--method", help="method name filter (substring)")
    ap.add_argument("--token", help="method token, e.g. 0x600e957")
    ap.add_argument("--search", help="search type and method names for a substring")
    args = ap.parse_args(argv)

    meta = Metadata(args.metadata)
    pe = Pe(args.dll)
    mapper = RvaMapper(meta, pe)

    if args.list_images:
        cmd_list_images(meta, mapper)
        return 0
    if args.stats:
        cmd_stats(meta, mapper)
        return 0

    if args.token:
        token = int(args.token, 0)
        info = mapper.rva_for_token(token)
        if not info:
            print("token %#x: no RVA (not in a known image or abstract method)" % token)
            return 1
        print("token %#x -> rva %#x  slot %#x  image %s  tableBase %#x"
              % (token, info["rva"], info["slot"], info["image"], info["image_base"]))
        return 0

    if args.search:
        needle = args.search.lower()
        print("== types ==")
        for t in find_types(meta, args.search):
            ns = (t["namespace"] + ".") if t["namespace"] else ""
            print("  %5d  %s%s  token=%#x  methods=%d" % (t["index"], ns, t["name"], t["token"], t["method_count"]))
        print("== methods ==")
        shown = 0
        for mi in range(meta.method_count):
            m = meta.method(mi)
            if needle in (m["name"] or "").lower():
                info = mapper.rva_for_method(m)
                rva = info["rva"] if info else 0
                print("  idx=%6d  tok=%#x  rva=%#010x  %s" % (mi, m["token"], rva, m["name"]))
                shown += 1
                if shown >= 200:
                    print("  ... (truncated)")
                    break
        return 0

    if args.type_index is not None:
        print_type(meta, mapper, meta.type(args.type_index), args.method)
        return 0

    if args.type:
        hits = [t for t in find_types(meta, args.type) if t["name"] == args.type]
        if not hits:
            hits = find_types(meta, args.type)
        if not hits:
            print("no type matching %r" % args.type)
            return 1
        for t in hits:
            print_type(meta, mapper, t, args.method)
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
