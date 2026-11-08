#pragma once

// ============================================================================
//  Rust-Offset-Dumper / Resolver.h
//
//  Port of the offset-resolution tricks used by "Vlone Rust Internal"
//  (Data/Decryptors.h, Features/Chain/ChainScan.h, Features/Chain/ClassScan.h).
//
//  Their dumper/cheat never trusts a number it did not verify. Four layers:
//
//   1) TYPEINFO SLOTS - the RVA is only accepted when
//        slot(GameAssembly + rva) == klass  &&  klass+0x10 -> printable name
//      A slot that EAC garbage-filled dies here instead of being used.
//
//   2) STATIC BLOCK - three paths, tried in order:
//        a) il2cpp_class_get_static_field_data export
//        b) klass + 0xB8                     (Il2CppClass::static_fields)
//        c) protection wrapper: klass+0x28 -> klass, then wrapper+0xB8
//      The wrapper path is what saved them when the export returned garbage.
//
//   3) ENTITY CHAIN - no hardcoded realm offset. Every plausible static slot
//      (0x08..0x80) is decrypted with both runtime decryptors and the result is
//      judged by SHAPE (List<T> / Il2Cpp array), by population and by whether
//      the elements are real managed objects. The winner is written down.
//
//   4) COLLECTION SWEEP - only when the chain could not be proven: walk every
//      class' static block, read every static field, keep the biggest
//      collection that passes the same shape test (ClassScan).
//
//  Everything this file emits is measured at dump time. Nothing is guessed:
//  an unverifiable slot is written as verified = false, never as a fake RVA.
// ============================================================================

#include "Il2Cpp.h"
#include "generated/TypeInfoSeeds.generated.h"
#include "generated/TypeInfoTokens.generated.h"

namespace res
{
    // ---------------------------------------------------------------- types
    enum class Shape { None, Array, List };

    inline const char* ShapeName(Shape s)
    {
        switch (s)
        {
        case Shape::Array: return "Il2CppArray";
        case Shape::List:  return "List<T>";
        default:           return "none";
        }
    }

    struct Collection
    {
        u64   obj      = 0;   // collection object
        u64   data     = 0;   // element base
        u32   count    = 0;
        u32   arrayLen = 0;
        u32   countOff = 0;   // where the count lives, relative to obj
        u32   dataOff  = 0;   // where the element base lives, relative to obj
        Shape shape    = Shape::None;
        bool  populated = false;
    };

    // ---------------------------------------------------------------- helpers
    // A managed object slot is good if it is null (List<T> keeps holes) or if
    // *obj points at a klass whose +0x10 name pointer is printable. This is the
    // exact check ClassScan::LooksLikeManagedObject performs, but without any
    // il2cpp accessor (a bad accessor must not be able to fault the probe).
    inline bool IsManagedSlot(u64 o)
    {
        if (!o) return true;
        if (!MemReadable(o, 0x20)) return false;
        u64 klass = ReadPtr(o);
        if (!klass || !MemReadable(klass, 0x40)) return false;
        u64 namePtr = ReadPtr(klass + 0x10);
        if (!namePtr || !MemReadable(namePtr, 2)) return false;
        char c = 0;
        if (!SafeRead(namePtr, c)) return false;
        return c >= 0x20 && c <= 0x7E;
    }

    inline u32 ElementScore(u64 data, u32 count)
    {
        u32 probe = count < 4 ? count : 4;
        u32 nonNull = 0, same = 0;
        u64 first = 0;
        for (u32 i = 0; i < probe; ++i)
        {
            u64 e = ReadPtr(data + (u64)i * 8);
            if (!e || !IsManagedSlot(e)) continue;
            u64 k = ReadPtr(e);
            if (!k) continue;
            if (!first) first = k;
            if (k == first) ++same;
            ++nonNull;
        }
        if (!nonNull) return 0;
        // a homogeneous list of managed objects is what an entity list looks like
        return (same * 1000u) / nonNull;
    }

    // ---------------------------------------------------------------- shape
    // Recognises the two layouts Rust actually uses for entity storage:
    //   Il2Cpp array : +0x18 length, elements from +0x20
    //   List<T>      : +0x08 items[], +0x10 count, +0x18 version
    //
    // allowEmpty = accept a structurally valid but empty collection (main menu).
    // A populated hit always outranks an empty one - see ProbeRealmSlot.
    inline bool Classify(u64 p, Collection* out, bool allowEmpty = false,
                         const char** why = nullptr)
    {
        if (out) *out = Collection{};
        if (why) *why = "";

        if (!p)
        {
            if (why) *why = "null";
            return false;
        }
        if (!MemReadable(p, 0x40))
        {
            if (why) *why = "object not readable";
            return false;
        }

        // --- Il2Cpp array: klass +0x00, bounds +0x10, length +0x18, data +0x20
        {
            u32 len = ReadU32(p + 0x18);
            if (len <= 0x40000 && MemReadable(p + 0x20, 8))
            {
                u64 data = p + 0x20;
                if (len == 0)
                {
                    if (allowEmpty)
                    {
                        if (out)
                        {
                            out->obj = p; out->data = data; out->count = 0;
                            out->countOff = 0x18; out->dataOff = 0x20;
                            out->shape = Shape::Array; out->populated = false;
                        }
                        return true;
                    }
                }
                else
                {
                    u32 score = ElementScore(data, len);
                    if (score > 0)
                    {
                        if (out)
                        {
                            out->obj = p; out->data = data;
                            out->count = len; out->arrayLen = len;
                            out->countOff = 0x18; out->dataOff = 0x20;
                            out->shape = Shape::Array; out->populated = true;
                        }
                        return true;
                    }
                    if (why) *why = "array elements are not managed objects";
                }
            }
            else if (why && !*why && len > 0x40000)
            {
                *why = "array length out of range";
            }
        }

        // --- List<T>: +0x08 items[], +0x10 count, +0x18 version
        {
            u64 items = ReadPtr(p + 0x08);
            u32 cnt = ReadU32(p + 0x10);
            if (!items || !MemReadable(items + 0x18, 0x10))
            {
                if (why && !*why) *why = "not an array, no List<T> backing array";
            }
            else
            {
                u32 alen = ReadU32(items + 0x18);
                u64 data = items + 0x20;
                if (alen > 0x40000 || alen < cnt)
                {
                    if (why && !*why) *why = "List<T> count/capacity mismatch";
                }
                else if (cnt == 0)
                {
                    if (allowEmpty)
                    {
                        if (out)
                        {
                            out->obj = p; out->data = data; out->count = 0;
                            out->arrayLen = alen;
                            out->countOff = 0x10; out->dataOff = 0x08;
                            out->shape = Shape::List; out->populated = false;
                        }
                        return true;
                    }
                    if (why && !*why) *why = "List<T> is empty (no population)";
                }
                else
                {
                    u32 probe = cnt < 8 ? cnt : 8;
                    if (!MemReadable(data, (size_t)probe * 8))
                    {
                        if (why && !*why) *why = "List<T> element span unreadable";
                    }
                    else if (ElementScore(data, cnt) == 0)
                    {
                        if (why && !*why) *why = "List<T> elements are not managed objects";
                    }
                    else
                    {
                        if (out)
                        {
                            out->obj = p; out->data = data;
                            out->count = cnt; out->arrayLen = alen;
                            out->countOff = 0x10; out->dataOff = 0x08;
                            out->shape = Shape::List; out->populated = true;
                        }
                        return true;
                    }
                }
            }
        }
        return false;
    }

    // ---------------------------------------------------------------- (1) typeinfo
    struct ResolvedSlot
    {
        std::string name;         // "ns::Class"
        std::string ident;        // sanitised C++ identifier
        u64         klass = 0;
        u32         rva = 0;      // GameAssembly-relative slot, 0 = none found
        bool        verified = false;   // slot held the live klass pointer
        bool        seeded = false;     // RVA came from the community seed table
        bool        computed = false;   // RVA found by scanning for the metadata token
        // When statics live in a sibling "<Name>Static" class, record the
        // sibling's own live klass and its already-scanned TypeInfo slot.
        // Both values come from the dump, never from a hardcoded table.
        u64         aliasKlass = 0;
        u32         aliasTypeinfoRva = 0;
        bool        lazy = false;       // slot still holds a TypeInfo usage token
        u32         usageIndex = 0;     // decoded token index when lazy
        u64         staticBlock = 0;
        std::string staticVia;    // "export" / "klass+0xB8" / "wrapper+0xB8" / "none"
    };

    inline bool ValidKlass(u64 k)
    {
        if (!k || !MemReadable(k, 0x80)) return false;
        u64 namePtr = ReadPtr(k + 0x10);
        if (namePtr && MemReadable(namePtr, 2))
        {
            char c = 0;
            if (SafeRead(namePtr, c) && c >= 0x20 && c <= 0x7E)
                return true;
        }
        // fall back to the accessor if the raw layout differs on this build
        return !il2::KlassName((il2::Il2CppClass*)k).empty();
    }

    inline bool VerifySlot(const DumpResult& r, u64 klass, u32 rva, std::string* why)
    {
        if (why) why->clear();
        if (!r.gameAssembly || !rva)
        {
            if (why) *why = "no rva";
            return false;
        }
        u64 v = ReadPtr(r.gameAssembly + rva);
        if (v != klass)
        {
            if (why)
            {
                char b[96];
                sprintf_s(b, sizeof(b), "slot holds 0x%llX, not this klass",
                    (unsigned long long)v);
                *why = b;
            }
            return false;
        }
        if (!ValidKlass(v))
        {
            if (why) *why = "slot value is not a klass (bad name pointer)";
            return false;
        }
        return true;
    }

    inline const typeinfo_seeds::Seed* FindTypeInfoSeed(const std::string& name)
    {
        for (const auto& s : typeinfo_seeds::seeds)
            if (name == s.klass)
                return &s;
        return nullptr;
    }

    inline const typeinfo_tokens::Token* FindTypeInfoToken(const std::string& name)
    {
        for (const auto& t : typeinfo_tokens::tokens)
            if (name == t.klass)
                return &t;
        return nullptr;
    }

    // IL2CPP stores not-yet-initialised TypeInfo slots as a metadata usage
    // token: (kind << 29) | (index << 1) | 1, kind 1 == kTypeInfo.  The slot is
    // patched to the real Il2CppClass* the first time the generated method
    // metadata is initialised.  A seeded RVA is accepted only when the slot is
    // either that exact klass or one of these well-formed tokens.
    inline bool VerifySeededSlot(const DumpResult& r, u64 klass, u32 rva,
                                 bool* lazy, u32* usageIndex, std::string* why)
    {
        if (lazy) *lazy = false;
        if (usageIndex) *usageIndex = 0;
        if (why) why->clear();
        if (!r.gameAssembly || !rva)
        {
            if (why) *why = "no rva";
            return false;
        }
        u64 v = ReadPtr(r.gameAssembly + rva);
        if (v == klass && ValidKlass(v))
            return true;

        u32 t = (u32)v;
        u32 kind = t >> 29;
        u32 index = (t >> 1) & 0x0FFFFFFFu;
        if (v <= 0xFFFFFFFFull && (t & 1u) && kind == 1u && index)
        {
            if (lazy) *lazy = true;
            if (usageIndex) *usageIndex = index;
            return true;
        }

        if (why)
        {
            char b[128];
            sprintf_s(b, sizeof(b),
                "seed slot holds 0x%llX (not klass, not a TypeInfo usage token)",
                (unsigned long long)v);
            *why = b;
        }
        return false;
    }

    // path a: export, path b: klass+0xB8, path c: protection wrapper
    // `detail` (optional) receives one line explaining every path that failed.
    inline u64 StaticBlock(u64 klass, std::string* via, std::string* detail = nullptr)
    {
        if (via) *via = "none";
        if (detail) detail->clear();
        if (!klass || !MemReadable(klass, 0xC0))
        {
            if (detail) *detail = "klass unreadable";
            return 0;
        }

        u64 viaExport = 0, viaB8 = 0, viaWrapper = 0, wrapper = 0;
        bool exportFaulted = false;

        if (il2::class_get_static_field_data)
        {
            u64 s = 0;
            __try { s = (u64)il2::class_get_static_field_data((il2::Il2CppClass*)klass); }
            __except (EXCEPTION_EXECUTE_HANDLER) { s = 0; exportFaulted = true; }
            if (s && MemReadable(s, 0x20))
            {
                if (via) *via = "export";
                return s;
            }
            viaExport = s;
        }

        {
            u64 s = ReadPtr(klass + 0xB8);
            if (s && MemReadable(s, 0x20))
            {
                if (via) *via = "klass+0xB8";
                return s;
            }
            viaB8 = s;
        }

        {
            wrapper = ReadPtr(klass + 0x28);
            if (wrapper && wrapper != klass && MemReadable(wrapper, 0xC0))
            {
                u64 wname = ReadPtr(wrapper + 0x10);
                char c = 0;
                if (wname && MemReadable(wname, 2) && SafeRead(wname, c) && c >= 0x20 && c <= 0x7E)
                {
                    u64 ws = ReadPtr(wrapper + 0xB8);
                    if (ws && MemReadable(ws, 0x20))
                    {
                        if (via) *via = "wrapper+0xB8";
                        return ws;
                    }
                    viaWrapper = ws;
                }
            }
        }

        if (detail)
        {
            char b[256];
            sprintf_s(b, sizeof(b),
                "export=%s0x%llX klass+0xB8=0x%llX wrapper=0x%llX wrapper+0xB8=0x%llX",
                il2::class_get_static_field_data ? (exportFaulted ? "FAULT/" : "") : "missing/",
                (unsigned long long)viaExport,
                (unsigned long long)viaB8,
                (unsigned long long)wrapper,
                (unsigned long long)viaWrapper);
            *detail = b;
        }
        return 0;
    }

    // EAC/IL2CPP can split a class' static storage into a sibling
    // "<Name>Static" class (same hashed name family, parent Object, no instance
    // fields).  BaseNetworkable on 26140533 is exactly that case: the real
    // klass has static_fields == 0, while BaseNetworkableStatic owns the block.
    // Try the normal paths first, then the sibling only when it really owns a
    // readable static block.  The chain probe still has to prove the contents,
    // so this never turns an unverified guess into an offset.
    inline u64 StaticBlockForClass(const DumpResult& r, u64 klass,
                                   const std::string& name,
                                   std::string* via, std::string* detail,
                                   u64* aliasKlass = nullptr,
                                   u32* aliasTypeinfoRva = nullptr)
    {
        u64 stat = StaticBlock(klass, via, detail);
        if (stat)
            return stat;

        std::string alias = name;
        if (alias.size() < 6 || alias.compare(alias.size() - 6, 6, "Static") != 0)
            alias += "Static";

        for (const auto& c : r.classes)
        {
            if (c.name != alias)
                continue;

            std::string aliasDetail;
            std::string aliasVia;
            u64 astat = StaticBlock((u64)c.klass, &aliasVia, &aliasDetail);
            if (!astat)
                continue;

            if (via) *via = "alias:" + alias;
            if (aliasKlass) *aliasKlass = (u64)c.klass;

            // The sibling class often has its own TypeInfo slot already found by
            // the scan.  Record it so consumers can resolve "<Name>Static"
            // directly instead of repeating the name lookup at runtime.
            if (aliasTypeinfoRva)
            {
                auto ait = r.typeInfoRvas.find((u64)c.klass);
                if (ait != r.typeInfoRvas.end())
                {
                    for (u32 rva : ait->second)
                    {
                        std::string why;
                        if (VerifySlot(r, (u64)c.klass, rva, &why))
                        {
                            *aliasTypeinfoRva = rva;
                            break;
                        }
                    }
                }
            }
            if (detail)
            {
                if (!detail->empty()) *detail += "; ";
                *detail += "alias=" + alias + " klass=0x";
                char b[32];
                sprintf_s(b, sizeof(b), "%llX", (unsigned long long)c.klass);
                *detail += b;
            }
            Log("[RESOLVE]   static block=0x%llX via alias:%s klass=0x%llX",
                (unsigned long long)astat, alias.c_str(), (unsigned long long)c.klass);
            return astat;
        }
        return 0;
    }

    inline void ResolveSlots(const DumpResult& r, std::vector<ResolvedSlot>& out)
    {
        out.clear();
        size_t targets = 0, ok = 0, noSlot = 0, badSlot = 0, noStatic = 0;
        size_t seededCount = 0, computedCount = 0;
        size_t viaExport = 0, viaB8 = 0, viaWrapper = 0, viaAlias = 0;

        Log("[RESOLVE] checking %zu typeinfo slot mapping(s) against %zu live class(es)",
            r.typeInfoRvas.size(), r.classes.size());

        for (const auto& c : r.classes)
        {
            if (!c.target) continue;
            ++targets;

            ResolvedSlot s;
            s.name = c.ns.empty() ? c.name : (c.ns + "::" + c.name);
            s.ident = SanitizeIdent(c.name);
            s.klass = (u64)c.klass;

            auto it = r.typeInfoRvas.find((u64)c.klass);
            if (it == r.typeInfoRvas.end() || it->second.empty())
            {
                Log("[RESOLVE][MISS] %-42s klass=0x%llX  no data-section qword equals this klass",
                    s.name.c_str(), (unsigned long long)s.klass);
            }
            else
            {
                std::vector<u32> rvas = it->second;
                std::sort(rvas.begin(), rvas.end());

                char list[256]{};
                int pos = 0;
                for (u32 rva : rvas)
                {
                    if (pos < (int)sizeof(list) - 16)
                        pos += sprintf_s(list + pos, sizeof(list) - pos, " 0x%X", rva);
                }
                Log("[RESOLVE] %-42s klass=0x%llX candidates:%s",
                    s.name.c_str(), (unsigned long long)s.klass, list);

                for (u32 rva : rvas)
                {
                    std::string why;
                    if (VerifySlot(r, (u64)c.klass, rva, &why))
                    {
                        s.rva = rva;
                        s.verified = true;
                        Log("[RESOLVE]   ACCEPT rva=0x%X  slot(ga+0x%X)=0x%llX  klass name ok",
                            rva, rva, (unsigned long long)ReadPtr(r.gameAssembly + rva));
                        break;
                    }
                    Log("[RESOLVE]   reject rva=0x%X  %s", rva, why.c_str());
                }
            }

            // Fallback: community klass_rvas seed.  The slot is still read and
            // must be either this klass or a well-formed lazy TypeInfo token.
            if (!s.verified)
            {
                const typeinfo_seeds::Seed* seed = FindTypeInfoSeed(c.name);
                if (seed)
                {
                    std::string why;
                    bool lazy = false;
                    u32 usage = 0;
                    if (VerifySeededSlot(r, (u64)c.klass, seed->rva, &lazy, &usage, &why))
                    {
                        s.rva = seed->rva;
                        s.seeded = true;
                        s.lazy = lazy;
                        s.usageIndex = usage;
                        if (lazy)
                            Log("[RESOLVE]   SEED ACCEPT rva=0x%X  lazy TypeInfo token index=0x%X (slot not patched yet)",
                                s.rva, usage);
                        else
                            Log("[RESOLVE]   SEED ACCEPT rva=0x%X  slot now equals klass",
                                s.rva);
                    }
                    else
                    {
                        Log("[RESOLVE]   seed reject rva=0x%X  %s", seed->rva, why.c_str());
                    }
                }
            }

            // No (valid) community seed: compute the class's lazy TypeInfo usage
            // token from metadata and use the slot the scan found holding it.
            if (!s.verified && !s.seeded)
            {
                const typeinfo_tokens::Token* tk = FindTypeInfoToken(c.name);
                if (tk)
                {
                    u32 token = 0x20000000u | (tk->index << 1) | 1u;
                    auto tit = r.typeInfoTokenRvas.find(token);
                    if (tit != r.typeInfoTokenRvas.end())
                    {
                        for (u32 rva : tit->second)
                        {
                            if (ReadPtr(r.gameAssembly + rva) == token)
                            {
                                s.rva = rva;
                                s.computed = true;
                                s.lazy = true;
                                s.usageIndex = tk->index;
                                Log("[RESOLVE]   TOKEN ACCEPT rva=0x%X  computed token=0x%X "
                                    "(TypeInfo index 0x%X, slot not patched yet)",
                                    rva, token, tk->index);
                                break;
                            }
                        }
                    }
                }
            }

            if (s.verified) ++ok;
            if (s.seeded) ++seededCount;
            if (s.computed) ++computedCount;
            if (!s.verified && !s.seeded && !s.computed) ++noSlot;

            std::string staticDetail;
            s.staticBlock = StaticBlockForClass(r, (u64)c.klass, c.name,
                                                &s.staticVia, &staticDetail,
                                                &s.aliasKlass, &s.aliasTypeinfoRva);
            if (s.staticBlock)
            {
                if (s.staticVia == "export") ++viaExport;
                else if (s.staticVia == "klass+0xB8") ++viaB8;
                else if (s.staticVia == "wrapper+0xB8") ++viaWrapper;
                else if (s.staticVia.rfind("alias:", 0) == 0) ++viaAlias;

                if (s.staticVia != "export" && s.staticVia.rfind("alias:", 0) != 0)
                {
                    Log("[RESOLVE]   static block=0x%llX via %s (export %s)",
                        (unsigned long long)s.staticBlock, s.staticVia.c_str(),
                        il2::class_get_static_field_data ? "failed/unreadable" : "missing");
                }
            }
            else
            {
                ++noStatic;
                Log("[RESOLVE]   static block NOT resolved (%s)", staticDetail.c_str());
            }

            out.push_back(std::move(s));
        }

        Log("[RESOLVE] summary: targets=%zu verified-live=%zu seeded=%zu computed=%zu "
            "unresolved=%zu no-static=%zu | static via export=%zu klass+0xB8=%zu wrapper=%zu alias=%zu",
            targets, ok, seededCount, computedCount, noSlot, noStatic,
            viaExport, viaB8, viaWrapper, viaAlias);
    }

    // ---------------------------------------------------------------- (3) chain
    struct ChainHit
    {
        bool        found = false;
        u32         realmOff = 0;
        u32         listOff = 0;
        u64         realm = 0;
        u64         list = 0;
        Collection  col;
        std::string decryptor;
        std::string via;          // "realm is the list" / "realm+off"
        u64         score = 0;
        bool        populationProven = false;
    };

    inline void ConsiderHit(ChainHit& best, u32 realmOff, u32 listOff,
                            const char* decryptor, const char* via,
                            u64 realm, u64 list, const Collection& col,
                            bool verbose)
    {
        // populated wins over structural; population dominates, element quality
        // breaks ties
        u64 score = col.populated
            ? (u64)col.count + (u64)ElementScore(col.data, col.count)
            : 0;

        if (best.found && score <= best.score)
            return;

        if (verbose)
        {
            Log("[CHAINSCAN]      ACCEPT realm+0x%02X -> %s via %s, %s count=%u populated=%d score=%llu",
                listOff, ShapeName(col.shape), decryptor, col.count,
                col.populated ? 1 : 0, (unsigned long long)score);
        }

        best.found = true;
        best.realmOff = realmOff;
        best.listOff = listOff;
        best.realm = realm;
        best.list = list;
        best.col = col;
        best.decryptor = decryptor ? decryptor : "";
        best.via = via ? via : "";
        best.score = score;
        best.populationProven = col.populated;
    }

    inline bool ProbeRealmSlot(u64 stat, u32 realmOff, ChainHit* out, bool verbose)
    {
        if (out) *out = ChainHit{};

        u64 raw = ReadPtr(stat + realmOff);
        if (!raw || raw < 0x10000)
        {
            if (verbose)
                Log("[CHAINSCAN]   stat+0x%02X raw=0x%llX - empty slot, skip",
                    realmOff, (unsigned long long)raw);
            return false;
        }

        struct Src { u64 v; const char* nm; };
        Src srcs[3];
        int ns = 0;
        srcs[ns++] = { raw, "direct" };
        u64 ce = ClientEntitiesDecrypt(raw);
        u64 el = EntityListDecrypt(raw);
        if (ce) srcs[ns++] = { ce, "ClientEntitiesDecrypt" };
        if (el) srcs[ns++] = { el, "EntityListDecrypt" };

        if (verbose)
        {
            Log("[CHAINSCAN]   stat+0x%02X raw=0x%llX", realmOff, (unsigned long long)raw);
            Log("[CHAINSCAN]      ClientEntitiesDecrypt -> 0x%llX   EntityListDecrypt -> 0x%llX",
                (unsigned long long)ce, (unsigned long long)el);
        }

        ChainHit best;
        for (int s = 0; s < ns; ++s)
        {
            u64 realm = ResolveHandle(srcs[s].v);
            if (!realm || !MemReadable(realm, 0x40))
            {
                if (verbose)
                    Log("[CHAINSCAN]      [%s] resolve -> 0x%llX (not a readable handle)",
                        srcs[s].nm, (unsigned long long)realm);
                continue;
            }

            if (verbose)
            {
                std::string kn = il2::KlassName((il2::Il2CppClass*)ReadPtr(realm));
                Log("[CHAINSCAN]      [%s] resolve -> 0x%llX klass='%s'",
                    srcs[s].nm, (unsigned long long)realm, kn.c_str());
            }

            // (a) the decrypted value is already the collection
            {
                const char* why = "";
                Collection col;
                if (Classify(realm, &col, false, &why))
                    ConsiderHit(best, realmOff, 0, srcs[s].nm, "realm is the list", realm, realm, col, verbose);
                else if (verbose)
                    Log("[CHAINSCAN]      [%s] realm itself: %s", srcs[s].nm, why);
            }

            // (b) the collection sits at realm+off, possibly encrypted again
            for (u32 lo = 0x08; lo <= 0x40; lo += 8)
            {
                u64 v = ReadPtr(realm + lo);
                if (!v || v < 0x10000)
                    continue;

                u64 variants[3] = { v, ClientEntitiesDecrypt(v), EntityListDecrypt(v) };
                const char* vn[3] = { "raw", "CE", "EL" };
                for (int k = 0; k < 3; ++k)
                {
                    if (!variants[k])
                        continue;
                    u64 lst = ResolveHandle(variants[k]);
                    if (!lst || !MemReadable(lst, 0x40))
                    {
                        if (verbose)
                            Log("[CHAINSCAN]      realm+0x%02X [%s] -> 0x%llX not readable",
                                lo, vn[k], (unsigned long long)lst);
                        continue;
                    }

                    const char* why = "";
                    Collection col;
                    if (Classify(lst, &col, false, &why))
                        ConsiderHit(best, realmOff, lo, srcs[s].nm, "realm+off", realm, lst, col, verbose);
                    else if (verbose)
                        Log("[CHAINSCAN]      realm+0x%02X [%s] -> 0x%llX rejected: %s",
                            lo, vn[k], (unsigned long long)lst, why);
                }
            }
        }

        if (best.found && out) *out = best;
        return best.found;
    }

    // Empty (structural) chain: only accepted when nothing populated was found.
    inline bool ProbeRealmSlotEmpty(u64 stat, u32 realmOff, ChainHit* out, bool verbose)
    {
        if (out) *out = ChainHit{};

        u64 raw = ReadPtr(stat + realmOff);
        if (!raw || raw < 0x10000)
            return false;

        u64 variants[3] = { raw, ClientEntitiesDecrypt(raw), EntityListDecrypt(raw) };
        const char* vn[3] = { "direct", "ClientEntitiesDecrypt", "EntityListDecrypt" };

        ChainHit best;
        for (int s = 0; s < 3; ++s)
        {
            if (!variants[s]) continue;
            u64 realm = ResolveHandle(variants[s]);
            if (!realm || !MemReadable(realm, 0x40)) continue;

            {
                Collection col;
                if (Classify(realm, &col, true) && !col.populated)
                    ConsiderHit(best, realmOff, 0, vn[s], "realm is an empty list", realm, realm, col, verbose);
            }
            for (u32 lo = 0x08; lo <= 0x40; lo += 8)
            {
                u64 v = ReadPtr(realm + lo);
                if (!v || v < 0x10000) continue;
                u64 lv[3] = { v, ClientEntitiesDecrypt(v), EntityListDecrypt(v) };
                for (int k = 0; k < 3; ++k)
                {
                    if (!lv[k]) continue;
                    u64 lst = ResolveHandle(lv[k]);
                    if (!lst || !MemReadable(lst, 0x40)) continue;
                    Collection col;
                    if (Classify(lst, &col, true) && !col.populated)
                        ConsiderHit(best, realmOff, lo, vn[s], "realm+off (empty)", realm, lst, col, verbose);
                }
            }
        }
        if (best.found && out) *out = best;
        return best.found;
    }

    inline u64 FindClassByName(const DumpResult& r, const char* name)
    {
        for (const auto& c : r.classes)
            if (c.name == name) return (u64)c.klass;
        return 0;
    }

    inline void LocateEntityChain(const DumpResult& r, ChainHit& out)
    {
        out = ChainHit{};

        u64 bn = FindClassByName(r, "BaseNetworkable");
        const char* how = "enumerated classes";
        if (!bn)
        {
            bn = (u64)il2::FindClass("", "BaseNetworkable");
            how = "il2cpp_class_from_name";
        }
        if (!bn) { bn = FindClassAnywhere("BaseNetworkable"); how = "FindClassAnywhere"; }

        Log("[CHAINSCAN] BaseNetworkable -> 0x%llX (%s)", (unsigned long long)bn, bn ? how : "NOT FOUND");
        if (!bn)
        {
            Log("[CHAINSCAN][!] class not found - chain probe skipped, rely on static sweep");
            return;
        }

        std::string via, staticDetail;
        u64 stat = StaticBlockForClass(r, bn, "BaseNetworkable", &via, &staticDetail);
        Log("[CHAINSCAN] static block=0x%llX via %s", (unsigned long long)stat, via.c_str());
        if (!stat || !MemReadable(stat, 0x90))
        {
            Log("[CHAINSCAN][!] static block unreachable (%s) - chain probe skipped",
                stat ? "range not readable" : staticDetail.c_str());
            return;
        }

        // one-time singleton dump, exactly what ChainScan::Locate prints so the
        // next build's offsets can be eyeballed without a debugger
        Log("[CHAINSCAN] --- BaseNetworkable static slots ---");
        for (u32 off = 0x08; off <= 0x80; off += 8)
        {
            u64 v = ReadPtr(stat + off);
            std::string kn;
            if (v && MemReadable(v, 0x30))
                kn = il2::KlassName((il2::Il2CppClass*)ReadPtr(v));
            Log("    stat+0x%02X = 0x%llX%s%s", off, (unsigned long long)v,
                kn.empty() ? "" : "  object '", kn.empty() ? "" : kn.c_str());
            if (!kn.empty()) Log("        (klass '%s')", kn.c_str());
        }
        Log("[CHAINSCAN] --- end slots ---");

        ChainHit populated, empty;
        DWORD t0 = GetTickCount();
        u32 probedSlots = 0, nonEmptySlots = 0;

        // highest slot first: BaseNetworkable keeps its collection at the tail
        for (int off = 0x80; off >= 0x08; off -= 8)
        {
            ChainHit hit;
            probedSlots++;
            u64 rawSlot = ReadPtr(stat + (u32)off);
            if (rawSlot && rawSlot >= 0x10000)
                nonEmptySlots++;
            if (ProbeRealmSlot(stat, (u32)off, &hit, true))
            {
                Log("[CHAINSCAN] slot +0x%02X survived: %s / %s, realm+0x%02X -> %s count=%u",
                    (u32)off, hit.decryptor.c_str(), hit.via.c_str(),
                    hit.listOff, ShapeName(hit.col.shape), hit.col.count);
                if (!populated.found || hit.score > populated.score)
                    populated = hit;
            }
            else if (ProbeRealmSlotEmpty(stat, (u32)off, &hit, false))
            {
                Log("[CHAINSCAN] slot +0x%02X survived as EMPTY %s at realm+0x%02X (structure only)",
                    (u32)off, ShapeName(hit.col.shape), hit.listOff);
                if (!empty.found || hit.score > empty.score)
                    empty = hit;
            }
        }

        Log("[CHAINSCAN] probe complete: %u static slot(s), %u non-empty, %lu ms",
            probedSlots, nonEmptySlots, GetTickCount() - t0);

        if (populated.found)
        {
            out = populated;
            Log("[CHAINSCAN][+] VERIFIED populated chain: realm +0x%02X, list +0x%02X, %s count=%u "
                "data_at=0x%02X via %s (%lu ms, score %llu)",
                out.realmOff, out.listOff, ShapeName(out.col.shape), out.col.count,
                out.col.dataOff, out.decryptor.c_str(),
                GetTickCount() - t0, (unsigned long long)out.score);
        }
        else if (empty.found)
        {
            out = empty;
            Log("[CHAINSCAN][~] only an EMPTY chain survived (main menu?): realm +0x%02X, list +0x%02X, %s "
                "(score 0, population NOT proven) - %lu ms",
                out.realmOff, out.listOff, ShapeName(out.col.shape), GetTickCount() - t0);
        }
        else
        {
            Log("[CHAINSCAN][!] no slot produced a verifiable collection after %lu ms "
                "(decryptors wrong for this build, or no session yet)",
                GetTickCount() - t0);
        }
    }

    // ---------------------------------------------------------------- (4) sweep
    struct SweepHit
    {
        u64         klass = 0;
        std::string className;
        std::string fieldName;
        u32         fieldOff = 0;
        u64         host = 0;
        Collection  col;
        u64         score = 0;
    };

    inline void SweepCollections(const DumpResult& r, std::vector<SweepHit>& out,
                                 DWORD budgetMs = 20000, u32 minCount = 32)
    {
        out.clear();
        if (r.classes.empty())
            return;

        DWORD t0 = GetTickCount();
        size_t walked = 0, withStatic = 0, fields = 0, matched = 0;
        DWORD lastReport = t0;

        Log("[SWEEP] ClassScan-style static collection sweep: %zu class(es), budget %lu ms, min population %u",
            r.classes.size(), budgetMs, minCount);

        for (const auto& c : r.classes)
        {
            if ((GetTickCount() - t0) >= budgetMs)
            {
                Log("[SWEEP][!] budget reached after %zu class(es) - partial result", walked);
                break;
            }
            ++walked;

            if (walked % 1000 == 0)
            {
                Log("[SWEEP] ... %zu/%zu classes, %zu with statics, %zu field(s), %zu match(es), %lu ms",
                    walked, r.classes.size(), withStatic, fields, matched, GetTickCount() - t0);
            }

            std::string via;
            u64 stat = StaticBlockForClass(r, (u64)c.klass, c.name, &via, nullptr);
            if (!stat || !MemReadable(stat, 0x20))
                continue;
            ++withStatic;

            void* iter = nullptr;
            int guard = 0;
            while (guard++ < 512)
            {
                il2::Il2CppField* f = nullptr;
                if (!il2::SafeClassGetFields((il2::Il2CppClass*)c.klass, &iter, &f))
                {
                    if (walked <= 32)
                        Log("[SWEEP]   field walk FAULT in %s - class skipped", c.name.c_str());
                    break;
                }
                if (!f || !MemReadable((u64)f, 0x20))
                    break;

                int flags = 0;
                if (!il2::SafeFieldFlags(f, &flags))
                    continue;
                if ((flags & 0x10) == 0)
                    continue;                       // instance field, not in static block

                size_t fo = 0;
                if (!il2::SafeFieldOffset(f, &fo))
                    continue;
                if (fo > 0x4000)
                    continue;
                ++fields;

                u64 val = ReadPtr(stat + fo);
                if (!val || !MemReadable(val, 0x40))
                    continue;

                const char* why = "";
                Collection col;
                if (!Classify(val, &col, false, &why))
                    continue;
                if (col.count < minCount)
                    continue;

                SweepHit h;
                h.klass = (u64)c.klass;
                h.className = c.ns.empty() ? c.name : (c.ns + "::" + c.name);
                h.fieldName = il2::FieldName(f);
                if (h.fieldName.empty())
                {
                    char nb[32];
                    sprintf_s(nb, sizeof(nb), "field_0x%X", (u32)fo);
                    h.fieldName = nb;
                }
                h.fieldOff = (u32)fo;
                h.host = stat;
                h.col = col;
                h.score = (u64)col.count + (u64)ElementScore(col.data, col.count);
                Log("[SWEEP][match] %s::%s +0x%X -> %s count=%u score=%llu (klass=0x%llX)",
                    h.className.c_str(), h.fieldName.c_str(), h.fieldOff,
                    ShapeName(col.shape), col.count, (unsigned long long)h.score,
                    (unsigned long long)h.klass);
                out.push_back(std::move(h));
                ++matched;
            }

            (void)lastReport;
        }

        std::sort(out.begin(), out.end(), [](const SweepHit& a, const SweepHit& b) {
            return a.score > b.score;
            });
        if (out.size() > 16)
            out.resize(16);

        Log("[SWEEP] done: %zu class(es), %zu with statics, %zu static field(s) read, "
            "%zu match(es), %zu kept (%lu ms)",
            walked, withStatic, fields, matched, out.size(), GetTickCount() - t0);

        for (size_t i = 0; i < out.size() && i < 5; ++i)
        {
            Log("[SWEEP]  #%zu %s::%s +0x%X -> %s count=%u score=%llu",
                i + 1, out[i].className.c_str(), out[i].fieldName.c_str(),
                out[i].fieldOff, ShapeName(out[i].col.shape), out[i].col.count,
                (unsigned long long)out[i].score);
        }
    }

    // ---------------------------------------------------------------- write
    inline void WriteResolved(const DumpResult& r,
                              const std::vector<ResolvedSlot>& slots,
                              const ChainHit& chain,
                              const std::vector<SweepHit>& sweep,
                              const std::string& path)
    {
        std::ofstream f(path, std::ios::binary);
        if (!f)
        {
            Log("[WRITE][!] cannot open %s", path.c_str());
            return;
        }

        Log("[WRITE] generating resolved offsets: %s", path.c_str());

        size_t verified = 0, withStatic = 0;
        for (const auto& s : slots)
        {
            if (s.verified) ++verified;
            if (s.staticBlock) ++withStatic;
        }

        f << "// ============================================================================\n";
        f << "//  Rust-Offset-Dumper resolved offsets - " << r.timestamp << "\n";
        f << "//\n";
        f << "//  Everything below was MEASURED at dump time, nothing here is a guess.\n";
        f << "//\n";
        f << "//  typeinfo_rva is accepted only when\n";
        f << "//      slot(GameAssembly + rva) == klass  &&  klass+0x10 -> printable name\n";
        f << "//  static block came from the export, klass+0xB8 or the protection wrapper.\n";
        f << "//  The entity chain was verified by decrypting the live list and checking\n";
        f << "//  its shape, population and that the elements are real managed objects.\n";
        f << "//\n";
        f << "//  GameAssembly base: 0x" << std::hex << r.gameAssembly << std::dec << "\n";
        f << "//  slots: " << slots.size() << "   verified: " << verified
          << "   with static block: " << withStatic << "\n";
        f << "// ============================================================================\n\n";
        f << "#pragma once\n";
        f << "#include <cstddef>\n";
        f << "#include <cstdint>\n\n";
        f << "namespace resolved\n{\n";

        // ---- per class slots
        std::set<std::string> used;
        for (const auto& s : slots)
        {
            std::string id = s.ident;
            std::string uniq = id;
            int n = 1;
            while (used.count(uniq))
                uniq = id + "_" + std::to_string(++n);
            used.insert(uniq);

            f << "    // " << s.name << "  klass=0x" << std::hex << s.klass << std::dec << "\n";
            f << "    namespace " << uniq << "\n    {\n";
            f << "        static constexpr std::uint32_t typeinfo_rva = 0x"
              << std::hex << s.rva << std::dec << ";";
            if (!s.verified && !s.seeded && !s.computed)
                f << "  // NOT FOUND / NOT VERIFIED on this build";
            else if (s.lazy)
                f << "  // " << (s.computed ? "computed" : "seeded")
                  << "; slot is a lazy TypeInfo usage token";
            f << "\n";
            f << "        static constexpr bool typeinfo_verified = "
              << (s.verified ? "true" : "false") << ";\n";
            f << "        static constexpr bool typeinfo_seeded = "
              << (s.seeded ? "true" : "false") << ";\n";
            f << "        static constexpr bool typeinfo_computed = "
              << (s.computed ? "true" : "false") << ";\n";
            if (s.lazy)
                f << "        // usage token index 0x" << std::hex << s.usageIndex
                  << std::dec << " (class not initialised at dump time)\n";
            f << "        static constexpr bool static_block_resolved = "
              << (s.staticBlock ? "true" : "false") << ";\n";
            if (s.staticBlock)
            {
                f << "        // runtime block 0x" << std::hex << s.staticBlock << std::dec
                  << " via " << s.staticVia << "\n";
                if (s.aliasKlass)
                {
                    f << "        // sibling class 0x" << std::hex << s.aliasKlass << std::dec
                      << " owns this block\n";
                    if (s.aliasTypeinfoRva)
                    {
                        f << "        static constexpr std::uint32_t static_typeinfo_rva = 0x"
                          << std::hex << s.aliasTypeinfoRva << std::dec << ";\n";
                        f << "        static constexpr bool static_typeinfo_verified = true;\n";
                    }
                    else
                    {
                        f << "        static constexpr std::uint32_t static_typeinfo_rva = 0x0;"
                          << "  // sibling slot not confirmed\n";
                        f << "        static constexpr bool static_typeinfo_verified = false;\n";
                    }
                    f << "        static constexpr std::uint64_t static_klass = 0x"
                      << std::hex << s.aliasKlass << std::dec << "ULL;\n";
                }
            }
            f << "    }\n\n";
        }

        // ---- verified static wrappers -------------------------------------
        // The metadata in this build hides the names of BaseNetworkable's
        // static fields, but the storage layout is still testable: a wrapper
        // has a populated flag byte at +0x10 and two encrypted words at +0x18.
        // We only emit a slot when BOTH the decryptor produced a pointer and
        // that pointer dereferences to a real managed class name.  This is how
        // the live-verified BaseNetworkableStatic+0x28 clientEntities slot was
        // found, and it keeps finding new slots without guessing offsets.
        bool wroteStatic = false;
        for (const auto& c : r.classes)
        {
            if (c.name != "BaseNetworkableStatic")
                continue;

            std::string via;
            u64 stat = StaticBlockForClass(r, (u64)c.klass, c.name, &via, nullptr);
            if (!stat || !MemReadable(stat, 0x90))
                continue;

            for (u32 off = 0x10; off <= 0x80; off += 8)
            {
                u64 raw = ReadPtr(stat + off);
                if (!raw || !MemReadable(raw, 0x40))
                    continue;

                u8 flag = 0;
                SafeRead(raw + 0x10, flag);
                if (!flag)
                    continue;

                struct Candidate { const char* decryptor; u64 value; };
                Candidate cands[2] = {
                    { "ClientEntitiesDecrypt", ClientEntitiesDecrypt(raw) },
                    { "EntityListDecrypt",     EntityListDecrypt(raw)     },
                };

                for (const auto& cd : cands)
                {
                    u64 v = cd.value;
                    if (!v || !MemReadable(v, 0x30))
                        continue;

                    std::string vn = il2::KlassName((void*)ReadPtr(v));
                    if (vn.empty())
                        continue;

                    if (!wroteStatic)
                    {
                        f << "    // ---------------------------------------------------------------------\n";
                        f << "    //  static fields proven live: wrapper -> decrypt -> readable object\n";
                        f << "    // ---------------------------------------------------------------------\n";
                        f << "    namespace verified_static_fields\n    {\n";
                        wroteStatic = true;
                    }

                    f << "        // " << c.name << " static+0x" << std::hex << off
                      << std::dec << " via " << cd.decryptor
                      << " -> object '" << vn << "'\n";
                    f << "        static constexpr std::uint32_t " << cd.decryptor
                      << "_off_0x" << std::hex << off << std::dec << " = 0x"
                      << std::hex << off << std::dec << ";\n";
                    f << "        static constexpr const char* " << cd.decryptor
                      << "_klass_0x" << std::hex << off << std::dec << " = \""
                      << vn << "\";\n";
                }
            }
        }
        if (wroteStatic)
            f << "    }\n\n";

        // ---- chain
        f << "    // ---------------------------------------------------------------------\n";
        f << "    //  verified entity chain (BaseNetworkable static block)\n";
        f << "    // ---------------------------------------------------------------------\n";
        const bool proven = chain.found && chain.populationProven;
        f << "    namespace entity_chain\n    {\n";
        // "verified" must mean population was proven.  A readable but EMPTY
        // structure found at the main menu is only a candidate, not an offset.
        f << "        static constexpr bool verified = " << (proven ? "true" : "false") << ";\n";
        f << "        static constexpr bool structure_found = " << (chain.found ? "true" : "false") << ";\n";
        f << "        // true only when a NON-EMPTY list was decrypted and its elements checked\n";
        f << "        static constexpr bool population_proven = " << (proven ? "true" : "false") << ";\n";
        if (proven)
        {
            f << "        static constexpr std::uint32_t realm_off = 0x" << std::hex << chain.realmOff << std::dec << ";\n";
            f << "        static constexpr std::uint32_t list_off  = 0x" << std::hex << chain.listOff << std::dec << ";\n";
            f << "        static constexpr std::uint32_t count_off = 0x" << std::hex << chain.col.countOff << std::dec << ";\n";
            f << "        static constexpr std::uint32_t data_off  = 0x" << std::hex << chain.col.dataOff << std::dec << ";\n";
            f << "        static constexpr std::uint32_t live_count = " << chain.col.count << ";\n";
            f << "        static constexpr const char* shape = \"" << ShapeName(chain.col.shape) << "\";\n";
            f << "        static constexpr const char* decryptor = \"" << chain.decryptor << "\";\n";
            f << "        static constexpr const char* via = \"" << chain.via << "\";\n";
        }
        else if (chain.found)
        {
            f << "        // NOT an offset yet: only an empty structure survived at dump time.\n";
            f << "        // candidate realm_off=0x" << std::hex << chain.realmOff
              << " list_off=0x" << chain.listOff
              << " count_off=0x" << chain.col.countOff
              << " data_off=0x" << chain.col.dataOff << std::dec
              << " shape=" << ShapeName(chain.col.shape)
              << " decryptor=" << chain.decryptor << "\n";
        }
        f << "    }\n\n";

        // ---- sweep candidates
        f << "    // ---------------------------------------------------------------------\n";
        f << "    //  ClassScan candidates: biggest verifiable static collections\n";
        f << "    //  (used when entity_chain.population_proven == false)\n";
        f << "    // ---------------------------------------------------------------------\n";
        f << "    namespace static_collections\n    {\n";
        f << "        static constexpr std::size_t count = " << sweep.size() << ";\n";
        for (size_t i = 0; i < sweep.size(); ++i)
        {
            const auto& h = sweep[i];
            f << "        // #" << i + 1 << "  " << h.className << "::" << h.fieldName
              << "  " << ShapeName(h.col.shape)
              << "  live_count=" << h.col.count
              << "  field_off=0x" << std::hex << h.fieldOff << std::dec
              << "  klass=0x" << std::hex << h.klass << std::dec << "\n";
        }
        f << "    }\n";
        f << "} // namespace resolved\n";

        f.flush();
        f.close();
        LogFileWritten(path);
    }
} // namespace res
