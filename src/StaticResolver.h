#pragma once

// ============================================================================
//  Rust-Offset-Dumper / StaticResolver.h
//
//  Live counterpart of revers/rev_binary.py: it locates the per-class
//  `Il2CppCodeGenModule::fieldOffsets` int32 array inside the *mapped*
//  GameAssembly image and uses it to (a) verify the offsets that
//  il2cpp_field_get_offset returned and (b) fill the slots whose metadata
//  name is an EAC hash and whose live accessor gave up.
//
//  How the table is pinned (and why this cannot pick a wrong array):
//
//    * one entry per metadata field in declaration order, statics included,
//    * 0x67676767 means "offset not stored in this table",
//    * the base is only accepted when *every* anchor (a field with a readable
//      name and a plausible live offset) has `table[order] == liveOffset`.
//
//  Anchors are fields whose metadata name is readable, because their live
//  offset is the one the runtime actually uses.  Hidden (%hash) fields are
//  never used as anchors - they are the slots this file exists to recover.
//
//  The table is a *fallback*.  A live value always wins; the table only fills
//  a slot that the live accessor could not produce.  Nothing is invented: a
//  poison entry stays a hole and is reported as such.
// ============================================================================

#include "Il2Cpp.h"
#include <vector>
#include <cstdio>

namespace staticscan
{
    constexpr int kPoison = 0x67676767;

    struct Anchor
    {
        u32 fieldOrder = 0;   // index in the metadata field list
        u32 offset = 0;       // offset measured live
    };

    struct TableHit
    {
        bool  found = false;
        u32   rva = 0;
        u32   entries = 0;
        int   anchors = 0;
        int   matched = 0;
        std::vector<int> values;
    };

    // Same 40-hex rule the rest of the dumper uses, without pulling Dumper.h in.
    inline bool HashLikeName(const std::string& s)
    {
        if (s.empty()) return true;
        size_t start = 0;
        if (s[0] == '%' || s[0] == '_') start = 1;
        if (s.size() - start != 40) return false;
        for (size_t i = start; i < s.size(); ++i)
        {
            const char c = s[i];
            const bool hex = (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f') ||
                             (c >= 'A' && c <= 'F');
            if (!hex) return false;
        }
        return true;
    }

    inline bool PlausibleOffset(u32 off)
    {
        return off >= 0x10 && off <= 0x100000;
    }

    inline int ReadI32(u64 addr)
    {
        int v = 0;
        SafeRead(addr, v);
        return v;
    }

    // Scan the non-executable section data for the one int32 array whose
    // anchored entries equal the live offsets.  Returns the best hit only when
    // every anchor matched.
    inline TableHit FindFieldOffsetTable(u64 gameAssembly,
                                         u32 fieldCount,
                                         const std::vector<Anchor>& anchors)
    {
        TableHit best;
        best.anchors = (int)anchors.size();
        if (!gameAssembly || anchors.size() < 3 || !fieldCount)
            return best;

        const std::vector<PeSection> sections = GetPeSections(gameAssembly);

        // .rdata first: the field-offset arrays live there, and a decoy match in
        // another data section must not win over the real one.
        auto scanSection = [&](const PeSection& s) -> bool
        {
            if (s.chars & IMAGE_SCN_MEM_EXECUTE)      // code sections hold no tables
                return false;
            if (s.vsize < 4 * (u64)(fieldCount + 1))
                return false;

            const u64 base = gameAssembly + s.va;
            const u64 end = base + s.vsize;
            if (!MemReadable(base, (size_t)std::min<u64>(s.vsize, 0x1000)))
                return false;

            const u64 firstIdx = anchors[0].fieldOrder;
            bool local = false;

            for (u64 p = base; p + 4 * (u64)fieldCount <= end; p += 4)
            {
                const int v0 = ReadI32(p + firstIdx * 4);
                if (v0 != (int)anchors[0].offset)
                    continue;

                int matched = 0;
                bool bad = false;
                for (const Anchor& a : anchors)
                {
                    const int v = ReadI32(p + (u64)a.fieldOrder * 4);
                    if (v != (int)a.offset)
                    {
                        bad = true;
                        break;
                    }
                    ++matched;
                }
                if (bad)
                    continue;

                if (!local || matched > best.matched)
                {
                    local = true;
                    best.found = true;
                    best.matched = matched;
                    best.rva = (u32)(p - gameAssembly);
                    best.entries = fieldCount;
                    best.values.assign((size_t)fieldCount, 0);
                    for (u32 i = 0; i < fieldCount; ++i)
                        best.values[i] = ReadI32(p + (u64)i * 4);
                }
            }
            return local;
        };

        for (const PeSection& s : sections)
            if (s.name == ".rdata" && scanSection(s))
                return best;
        for (const PeSection& s : sections)
            if (s.name != ".rdata")
                scanSection(s);

        return best;
    }
} // namespace staticscan
