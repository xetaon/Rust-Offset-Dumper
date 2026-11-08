#pragma once

// ============================================================================
//  Rust-Offset-Dumper / Il2Cpp.h
//
//  Live IL2CPP access layer.  Everything here is resolved from the exports of
//  GameAssembly.dll at dump time - no hardcoded RVAs, no metadata parsing.
//  Metadata v39 cannot be parsed offline by current public dumpers, so the only
//  honest source is the running runtime itself.
// ============================================================================

#include <windows.h>
#include <psapi.h>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>
#include <unordered_set>
#include <unordered_map>
#include <algorithm>

#pragma comment(lib, "psapi.lib")

using u8  = uint8_t;
using u16 = uint16_t;
using u32 = uint32_t;
using u64 = uint64_t;
using i32 = int32_t;
using i64 = int64_t;

// ---------------------------------------------------------------------------
//  safe memory access - VirtualQuery based, never faults on bad pointers
// ---------------------------------------------------------------------------
// Per-thread cache of the last proven-readable region.  Enumeration reads name
// pointers, class headers and text blobs that all live inside a handful of
// large heap regions; without this every single read pays a syscall.
struct ReadCache
{
    u64 base = 0;
    u64 end = 0;
    bool ok = false;
};

inline bool MemReadable(u64 addr, size_t size)
{
    if (!addr || addr < 0x10000)
        return false;

    u64 cur = addr;
    u64 end = addr + size;
    if (end < addr)
        return false;

    static thread_local ReadCache cache;
    if (size && cache.ok && addr >= cache.base && end <= cache.end)
        return true;

    u64 cachedBase = 0, cachedEnd = 0;
    bool cached = false;

    while (cur < end)
    {
        MEMORY_BASIC_INFORMATION mbi{};
        if (VirtualQuery((LPCVOID)cur, &mbi, sizeof(mbi)) != sizeof(mbi))
            return false;
        if (mbi.State != MEM_COMMIT)
            return false;
        if (mbi.Protect & (PAGE_NOACCESS | PAGE_GUARD))
            return false;

        const DWORD p = mbi.Protect & 0xFF;
        const bool readable =
            p == PAGE_READONLY || p == PAGE_READWRITE ||
            p == PAGE_WRITECOPY || p == PAGE_EXECUTE_READ ||
            p == PAGE_EXECUTE_READWRITE || p == PAGE_EXECUTE_WRITECOPY;
        if (!readable)
            return false;

        u64 regionEnd = (u64)mbi.BaseAddress + mbi.RegionSize;
        if (regionEnd <= cur)
            return false;
        cachedBase = (u64)mbi.BaseAddress;
        cachedEnd = regionEnd;
        cached = true;
        cur = regionEnd;
    }

    if (cached)
    {
        cache.base = cachedBase;
        cache.end = cachedEnd;
        cache.ok = true;
    }
    return true;
}

template <typename T>
inline bool SafeRead(u64 addr, T& out)
{
    if (!MemReadable(addr, sizeof(T)))
        return false;
    memcpy(&out, (const void*)addr, sizeof(T));
    return true;
}

inline u64 ReadPtr(u64 addr)      { u64 v = 0; SafeRead(addr, v); return v; }
inline u32 ReadU32(u64 addr)      { u32 v = 0; SafeRead(addr, v); return v; }
inline u64 ReadU64(u64 addr)      { u64 v = 0; SafeRead(addr, v); return v; }
inline float ReadF32(u64 addr)    { float v = 0; SafeRead(addr, v); return v; }

inline std::string ReadCStr(u64 addr, size_t maxLen = 256)
{
    std::string s;
    if (!addr)
        return s;

    // Read in chunks instead of one SafeRead() per character: every SafeRead
    // runs VirtualQuery, and class names are read for 10k+ classes during
    // enumeration.  A readable chunk is memcpy'd at once; a page boundary or
    // unreadable page falls back to the byte-by-byte path.
    u64 cur = addr;
    u64 end = addr + maxLen;
    while (cur < end)
    {
        size_t chunk = (size_t)(end - cur);
        if (chunk > 64) chunk = 64;

        char buf[64];
        bool got = false;
        while (chunk > 0)
        {
            if (MemReadable(cur, chunk))
            {
                memcpy(buf, (const void*)cur, chunk);
                got = true;
                break;
            }
            chunk /= 2;
        }
        if (!got)
            break;

        for (size_t i = 0; i < chunk; ++i)
        {
            const char c = buf[i];
            if (!c)
                return s;
            if ((unsigned char)c < 0x20 && c != '\t')
            {
                s += '?';
                continue;
            }
            s += c;
        }
        cur += chunk;
    }
    return s;
}

inline bool StrEq(const char* a, const char* b)
{
    if (!a || !b) return false;
    while (*a && *b) { if (*a != *b) return false; ++a; ++b; }
    return *a == *b;
}

inline bool StrContainsI(const std::string& hay, const char* needle)
{
    if (!needle || !*needle) return true;
    std::string h = hay, n = needle;
    std::transform(h.begin(), h.end(), h.begin(), [](unsigned char c) { return (char)tolower(c); });
    std::transform(n.begin(), n.end(), n.begin(), [](unsigned char c) { return (char)tolower(c); });
    return h.find(n) != std::string::npos;
}

// ---------------------------------------------------------------------------
//  module helpers
// ---------------------------------------------------------------------------
inline u64 GetGameAssemblyBase()
{
    HMODULE h = GetModuleHandleA("GameAssembly.dll");
    if (h)
        return (u64)h;

    // x64 Rust: GameAssembly is always loaded. Fall back to ldr scan by name.
    HMODULE mods[1024]{};
    DWORD needed = 0;
    if (EnumProcessModules(GetCurrentProcess(), mods, sizeof(mods), &needed))
    {
        const DWORD count = needed / sizeof(HMODULE);
        for (DWORD i = 0; i < count; ++i)
        {
            char name[MAX_PATH]{};
            if (GetModuleBaseNameA(GetCurrentProcess(), mods[i], name, MAX_PATH))
            {
                if (StrEq(name, "GameAssembly.dll"))
                    return (u64)mods[i];
            }
        }
    }
    return 0;
}

struct PeSection
{
    std::string name;
    u64  va = 0;
    u64  vsize = 0;
    u64  raw = 0;
    u32  chars = 0;
};

inline std::vector<PeSection> GetPeSections(u64 base)
{
    std::vector<PeSection> out;
    if (!MemReadable(base, 0x1000))
        return out;

    auto dos = (PIMAGE_DOS_HEADER)base;
    if (dos->e_magic != IMAGE_DOS_SIGNATURE)
        return out;
    if (dos->e_lfanew <= 0 || dos->e_lfanew > 0x1000)
        return out;
    if (!MemReadable(base + dos->e_lfanew, sizeof(IMAGE_NT_HEADERS64)))
        return out;

    auto nt = (PIMAGE_NT_HEADERS64)(base + dos->e_lfanew);
    if (nt->Signature != IMAGE_NT_SIGNATURE)
        return out;

    const unsigned numberOfSections = nt->FileHeader.NumberOfSections;
    if (!numberOfSections || numberOfSections > 96)
        return out;
    if (!MemReadable((u64)IMAGE_FIRST_SECTION(nt),
                     (u64)numberOfSections * sizeof(IMAGE_SECTION_HEADER)))
        return out;

    auto sec = IMAGE_FIRST_SECTION(nt);
    for (int i = 0; i < nt->FileHeader.NumberOfSections; ++i, ++sec)
    {
        PeSection s;
        char nm[9]{};
        memcpy(nm, sec->Name, 8);
        s.name = nm;
        s.va = sec->VirtualAddress;
        s.vsize = sec->Misc.VirtualSize ? sec->Misc.VirtualSize : sec->SizeOfRawData;
        s.raw = sec->PointerToRawData;
        s.chars = sec->Characteristics;
        out.push_back(s);
    }
    return out;
}

inline u64 GetPeSizeOfImage(u64 base)
{
    if (!base || !MemReadable(base, 0x40))
        return 0;
    auto dos = (PIMAGE_DOS_HEADER)base;
    if (dos->e_magic != IMAGE_DOS_SIGNATURE)
        return 0;
    if (dos->e_lfanew <= 0 || dos->e_lfanew > 0x1000)
        return 0;
    if (!MemReadable(base + dos->e_lfanew, sizeof(IMAGE_NT_HEADERS64)))
        return 0;
    auto nt = (PIMAGE_NT_HEADERS64)(base + dos->e_lfanew);
    if (nt->Signature != IMAGE_NT_SIGNATURE)
        return 0;
    return nt->OptionalHeader.SizeOfImage;
}

// Returns the resolved VA, or 0.  `forwarder` (optional) receives the export
// forwarder string when the entry points outside the module.
inline u64 GetExportEx(u64 module, const char* name, const char** forwarder)
{
    if (forwarder) *forwarder = nullptr;
    if (!module || !name)
        return 0;

    HMODULE h = (HMODULE)module;
    if (FARPROC p = GetProcAddress(h, name))
        return (u64)p;

    // manual fallback (same logic the cheat uses)
    auto dos = (PIMAGE_DOS_HEADER)module;
    if (!MemReadable(module, 0x1000) || dos->e_magic != IMAGE_DOS_SIGNATURE)
        return 0;
    if (dos->e_lfanew <= 0 || dos->e_lfanew > 0x1000)
        return 0;
    if (!MemReadable(module + dos->e_lfanew, sizeof(IMAGE_NT_HEADERS64)))
        return 0;
    auto nt = (PIMAGE_NT_HEADERS64)(module + dos->e_lfanew);
    if (nt->Signature != IMAGE_NT_SIGNATURE)
        return 0;
    auto dir = (PIMAGE_DATA_DIRECTORY)&nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_EXPORT];
    if (!dir->VirtualAddress || !dir->Size)
        return 0;
    if (!MemReadable(module + dir->VirtualAddress, sizeof(IMAGE_EXPORT_DIRECTORY)))
        return 0;
    auto exp = (PIMAGE_EXPORT_DIRECTORY)(module + dir->VirtualAddress);
    const DWORD nNames = exp->NumberOfNames;
    if (!nNames || nNames > 100000)
        return 0;
    if (!MemReadable(module + exp->AddressOfFunctions, (u64)nNames * 4) ||
        !MemReadable(module + exp->AddressOfNames, (u64)nNames * 4) ||
        !MemReadable(module + exp->AddressOfNameOrdinals, (u64)nNames * 2))
        return 0;
    auto funcs = (DWORD*)(module + exp->AddressOfFunctions);
    auto names = (DWORD*)(module + exp->AddressOfNames);
    auto ords  = (WORD*)(module + exp->AddressOfNameOrdinals);
    for (DWORD i = 0; i < nNames; ++i)
    {
        const char* n = (const char*)(module + names[i]);
        if (!MemReadable((u64)n, 2))
            continue;
        if (StrEq(n, name))
        {
            const u32 ord = ords[i];
            const u64 rva = funcs[ord];
            const u64 expStart = module + dir->VirtualAddress;
            const u64 expEnd   = expStart + dir->Size;
            const u64 addr     = module + rva;
            if (addr >= expStart && addr < expEnd)
            {
                if (forwarder) *forwarder = (const char*)addr;
                return 0;
            }
            return addr;
        }
    }
    return 0;
}

inline u64 GetExport(u64 module, const char* name)
{
    return GetExportEx(module, name, nullptr);
}

// ---------------------------------------------------------------------------
//  IL2CPP exports used by the dumper
// ---------------------------------------------------------------------------
namespace il2
{
    using Il2CppClass    = void;
    using Il2CppField    = void;
    using Il2CppMethod   = void;
    using Il2CppType     = void;
    using Il2CppImage    = void;
    using Il2CppAssembly = void;

    using FnDomainGet            = void* (*)();
    using FnThreadAttach         = void* (*)(void*);
    using FnDomainGetAssemblies  = Il2CppAssembly** (*)(void*, size_t*);
    using FnAssemblyGetImage     = Il2CppImage* (*)(Il2CppAssembly*);
    using FnImageGetClassCount   = size_t (*)(Il2CppImage*);
    using FnImageGetClass        = Il2CppClass* (*)(Il2CppImage*, size_t);
    using FnImageGetName         = const char* (*)(Il2CppImage*);
    using FnClassGetName         = const char* (*)(Il2CppClass*);
    using FnClassGetNamespace    = const char* (*)(Il2CppClass*);
    using FnClassGetParent       = Il2CppClass* (*)(Il2CppClass*);
    using FnClassGetFields       = Il2CppField* (*)(Il2CppClass*, void**);
    using FnClassGetMethods      = Il2CppMethod* (*)(Il2CppClass*, void**);
    using FnClassGetStaticData   = void* (*)(Il2CppClass*);
    using FnClassGetType         = Il2CppType* (*)(Il2CppClass*);
    using FnClassFromName        = Il2CppClass* (*)(Il2CppImage*, const char*, const char*);
    using FnFieldGetName         = const char* (*)(Il2CppField*);
    using FnFieldGetOffset       = size_t (*)(Il2CppField*);
    using FnFieldGetFlags        = int (*)(Il2CppField*);
    using FnFieldGetType         = Il2CppType* (*)(Il2CppField*);
    using FnFieldStaticGetValue  = void (*)(Il2CppField*, void*);
    using FnMethodGetName        = const char* (*)(Il2CppMethod*);
    using FnMethodGetParamCount  = int (*)(Il2CppMethod*);
    using FnMethodGetParamName   = const char* (*)(Il2CppMethod*, int);
    using FnMethodGetParam       = Il2CppType* (*)(Il2CppMethod*, int);
    using FnTypeGetName          = const char* (*)(Il2CppType*);
    using FnTypeGetObject        = u64 (*)(Il2CppType*);
    using FnRuntimeClassInit     = void (*)(Il2CppClass*);
    using FnGcHandleGetTarget    = u64 (*)(u32);
    using FnRuntimeInvoke        = u64 (*)(Il2CppMethod*, u64, u64*, u64*);
    using FnObjectNew            = u64 (*)(Il2CppClass*);

    inline u64 module = 0;

    inline FnDomainGet           domain_get = nullptr;
    inline FnThreadAttach        thread_attach = nullptr;
    inline FnDomainGetAssemblies domain_get_assemblies = nullptr;
    inline FnAssemblyGetImage    assembly_get_image = nullptr;
    inline FnImageGetClassCount  image_get_class_count = nullptr;
    inline FnImageGetClass       image_get_class = nullptr;
    inline FnImageGetName        image_get_name = nullptr;
    inline FnClassGetName        class_get_name = nullptr;
    inline FnClassGetNamespace   class_get_namespace = nullptr;
    inline FnClassGetParent      class_get_parent = nullptr;
    inline FnClassGetFields      class_get_fields = nullptr;
    inline FnClassGetMethods     class_get_methods = nullptr;
    inline FnClassGetStaticData  class_get_static_field_data = nullptr;
    inline FnClassGetType        class_get_type = nullptr;
    inline FnClassFromName       class_from_name = nullptr;
    inline FnFieldGetName        field_get_name = nullptr;
    inline FnFieldGetOffset      field_get_offset = nullptr;
    inline FnFieldGetFlags       field_get_flags = nullptr;
    inline FnFieldGetType        field_get_type = nullptr;
    inline FnFieldStaticGetValue field_static_get_value = nullptr;
    inline FnMethodGetName       method_get_name = nullptr;
    inline FnMethodGetParamCount method_get_param_count = nullptr;
    inline FnMethodGetParamName  method_get_param_name = nullptr;
    inline FnMethodGetParam      method_get_param = nullptr;
    inline FnTypeGetName         type_get_name = nullptr;
    inline FnTypeGetObject       type_get_object = nullptr;
    inline FnRuntimeClassInit    runtime_class_init = nullptr;
    inline FnGcHandleGetTarget   gchandle_get_target = nullptr;
    inline FnRuntimeInvoke       runtime_invoke = nullptr;
    inline FnObjectNew           object_new = nullptr;

    inline bool ResolveExports(u64 gameAssembly)
    {
        module = gameAssembly;
        if (!module)
            return false;

    #define RE(v, n) v = (decltype(v))GetExport(module, n)
        RE(domain_get,            "il2cpp_domain_get");
        RE(thread_attach,         "il2cpp_thread_attach");
        RE(domain_get_assemblies, "il2cpp_domain_get_assemblies");
        RE(assembly_get_image,    "il2cpp_assembly_get_image");
        RE(image_get_class_count, "il2cpp_image_get_class_count");
        RE(image_get_class,       "il2cpp_image_get_class");
        RE(image_get_name,        "il2cpp_image_get_name");
        RE(class_get_name,        "il2cpp_class_get_name");
        RE(class_get_namespace,   "il2cpp_class_get_namespace");
        RE(class_get_parent,      "il2cpp_class_get_parent");
        RE(class_get_fields,      "il2cpp_class_get_fields");
        RE(class_get_methods,     "il2cpp_class_get_methods");
        RE(class_get_static_field_data, "il2cpp_class_get_static_field_data");
        RE(class_get_type,        "il2cpp_class_get_type");
        RE(class_from_name,       "il2cpp_class_from_name");
        RE(field_get_name,        "il2cpp_field_get_name");
        RE(field_get_offset,      "il2cpp_field_get_offset");
        RE(field_get_flags,       "il2cpp_field_get_flags");
        RE(field_get_type,        "il2cpp_field_get_type");
        RE(field_static_get_value, "il2cpp_field_static_get_value");
        RE(method_get_name,       "il2cpp_method_get_name");
        RE(method_get_param_count, "il2cpp_method_get_param_count");
        RE(method_get_param_name, "il2cpp_method_get_param_name");
        RE(method_get_param,      "il2cpp_method_get_param");
        RE(type_get_name,         "il2cpp_type_get_name");
        RE(type_get_object,       "il2cpp_type_get_object");
        RE(runtime_class_init,    "il2cpp_runtime_class_init");
        RE(gchandle_get_target,   "il2cpp_gchandle_get_target");
        RE(runtime_invoke,        "il2cpp_runtime_invoke");
        RE(object_new,            "il2cpp_object_new");
    #undef RE

        return domain_get && domain_get_assemblies && assembly_get_image &&
               image_get_class_count && image_get_class && class_get_fields;
    }

    // Raw accessors only - these use __try, so they must not contain any local
    // object that needs unwinding (MSVC C2712).
    inline const char* RawClassName(Il2CppClass* k)
    {
        if (!k || !class_get_name) return nullptr;
        __try { return class_get_name(k); }
        __except (EXCEPTION_EXECUTE_HANDLER) { return nullptr; }
    }

    inline const char* RawNamespace(Il2CppClass* k)
    {
        if (!k || !class_get_namespace) return nullptr;
        __try { return class_get_namespace(k); }
        __except (EXCEPTION_EXECUTE_HANDLER) { return nullptr; }
    }

    inline const char* RawTypeName(Il2CppType* t)
    {
        if (!t || !type_get_name) return nullptr;
        __try { return type_get_name(t); }
        __except (EXCEPTION_EXECUTE_HANDLER) { return nullptr; }
    }

    inline Il2CppType* RawFieldType(Il2CppField* f)
    {
        if (!f || !field_get_type) return nullptr;
        __try { return field_get_type(f); }
        __except (EXCEPTION_EXECUTE_HANDLER) { return nullptr; }
    }

    inline std::string KlassName(Il2CppClass* k)
    {
        // Il2CppClass::name is the pointer at +0x10 on this build (same field
        // the reference layout header calls klass_layout::name_ptr).  Reading it
        // directly avoids the protected class_get_name trampoline, which is the
        // single most expensive call during a 10k-class enumeration.  Fall back
        // to the export if the direct read yields nothing printable.
        if (k)
        {
            u64 np = ReadPtr((u64)k + 0x10);
            if (np && MemReadable(np, 1))
            {
                std::string s = ReadCStr(np, 192);
                if (!s.empty() && s.find('?') == std::string::npos)
                    return s;
            }
        }
        const char* n = RawClassName(k);
        return (n && MemReadable((u64)n, 1)) ? ReadCStr((u64)n, 192) : std::string();
    }

    inline std::string KlassNamespace(Il2CppClass* k)
    {
        // namespaze sits right after name (+0x18)
        if (k)
        {
            u64 np = ReadPtr((u64)k + 0x18);
            if (np && MemReadable(np, 1))
            {
                std::string s = ReadCStr(np, 192);
                if (s.find('?') == std::string::npos)
                    return s;
            }
        }
        const char* n = RawNamespace(k);
        return (n && MemReadable((u64)n, 1)) ? ReadCStr((u64)n, 192) : std::string();
    }

    inline std::string TypeName(Il2CppType* t)
    {
        const char* n = RawTypeName(t);
        return (n && MemReadable((u64)n, 1)) ? ReadCStr((u64)n, 192) : std::string();
    }

    // field -> Il2CppType -> printable name; used by every layout dump
    inline std::string FieldTypeName(Il2CppField* f)
    {
        Il2CppType* t = RawFieldType(f);
        if (!t)
            return std::string();
        return TypeName(t);
    }

    // -----------------------------------------------------------------------
    //  guarded metadata walk helpers - a protected class must never fault the
    //  whole enumeration, so every hot accessor goes through these.
    // -----------------------------------------------------------------------
    inline Il2CppImage* SafeAssemblyGetImage(Il2CppAssembly* a)
    {
        if (!a || !assembly_get_image) return nullptr;
        __try { return assembly_get_image(a); }
        __except (EXCEPTION_EXECUTE_HANDLER) { return nullptr; }
    }

    inline size_t SafeImageGetClassCount(Il2CppImage* img, bool* ok)
    {
        if (ok) *ok = false;
        if (!img || !image_get_class_count) return 0;
        __try { size_t n = image_get_class_count(img); if (ok) *ok = true; return n; }
        __except (EXCEPTION_EXECUTE_HANDLER) { return 0; }
    }

    inline Il2CppClass* SafeImageGetClass(Il2CppImage* img, size_t idx)
    {
        if (!img || !image_get_class) return nullptr;
        __try { return image_get_class(img, idx); }
        __except (EXCEPTION_EXECUTE_HANDLER) { return nullptr; }
    }

    // -----------------------------------------------------------------------
    //  fast class table
    //
    //  il2cpp_image_get_class goes through the protected export on this build
    //  (~30 ms per call, 32k classes => ~16 minutes).  IL2CPP itself keeps every
    //  linked Il2CppClass* in one flat array indexed by TypeDefinitionIndex, and
    //  Il2CppClass carries that index in a uint32 handle.  We locate the array
    //  once, then read klass pointers straight out of it.
    // -----------------------------------------------------------------------
    inline u32 ReadU32Raw(u64 addr) { u32 v = 0; SafeRead(addr, v); return v; }

    struct TypeTableInfo
    {
        u64 table = 0;      // &array[0], array[tdi] == Il2CppClass*
        u32 handleOffset = 0;
        bool valid = false;
    };

    inline TypeTableInfo& TypeTable()
    {
        static TypeTableInfo t;
        return t;
    }

    // cannot hold objects with destructors next to __try (MSVC C2712)
    inline u32 DetectHandleOffset(u64 k0, u64 k1, u64 k2)
    {
        for (u32 off = 0x40; off <= 0xA0; off += 4)
        {
            u32 v0 = ReadU32Raw(k0 + off);
            if (v0 == 0xFFFFFFFFu || v0 > 0x400000u) continue;
            if (ReadU32Raw(k1 + off) != v0 + 1) continue;
            if (ReadU32Raw(k2 + off) != v0 + 2) continue;
            return off;
        }
        return 0;
    }

    inline u64 ScanForTypeTable(u64 k0, u64 k1, u64 k2, u32 t0, u32 t1, u32 t2)
    {
        SYSTEM_INFO si{};
        GetSystemInfo(&si);
        u64 addr = (u64)si.lpMinimumApplicationAddress;
        u64 limit = (u64)si.lpMaximumApplicationAddress;
        const size_t CHUNK = 1 << 20;
        static thread_local std::vector<u8> buf;
        if (buf.size() < CHUNK) buf.resize(CHUNK);

        while (addr < limit)
        {
            MEMORY_BASIC_INFORMATION mbi{};
            if (VirtualQuery((LPCVOID)addr, &mbi, sizeof(mbi)) != sizeof(mbi))
                break;
            u64 base = (u64)mbi.BaseAddress;
            u64 next = base + mbi.RegionSize;
            if (next <= addr) break;

            const DWORD p = mbi.Protect & 0xFF;
            const bool readable = mbi.State == MEM_COMMIT && !(mbi.Protect & (PAGE_NOACCESS | PAGE_GUARD)) &&
                (p == PAGE_READONLY || p == PAGE_READWRITE || p == PAGE_WRITECOPY ||
                 p == PAGE_EXECUTE_READ || p == PAGE_EXECUTE_READWRITE || p == PAGE_EXECUTE_WRITECOPY);

            if (readable && mbi.Type == MEM_PRIVATE)
            {
                u64 end = base + mbi.RegionSize;
                for (u64 p2 = base; p2 + 8 <= end; )
                {
                    size_t chunk = (size_t)(std::min)((u64)CHUNK, end - p2);
                    memcpy(buf.data(), (const void*)p2, chunk);
                    u64 v0 = 0;
                    for (size_t i = 0; i + 8 <= chunk; i += 8)
                    {
                        memcpy(&v0, buf.data() + i, 8);
                        if (v0 != k0) continue;
                        u64 cand = p2 + i;
                        u64 tb = cand - 8ull * t0;
                        if (!tb) continue;
                        if (ReadPtr(tb + 8ull * t1) != k1) continue;
                        if (ReadPtr(tb + 8ull * t2) != k2) continue;
                        return tb;
                    }
                    p2 += chunk;
                }
            }
            addr = next;
        }
        return 0;
    }

    // probe: 3 protected calls, then one memory sweep (once per process)
    inline bool BuildTypeTable(Il2CppImage* probe, size_t count)
    {
        TypeTableInfo& tt = TypeTable();
        if (tt.valid) return true;
        if (!probe || count < 4) return false;

        u64 k0 = (u64)SafeImageGetClass(probe, 0);
        u64 k1 = (u64)SafeImageGetClass(probe, 1);
        u64 k2 = (u64)SafeImageGetClass(probe, 2);
        if (!k0 || !k1 || !k2) return false;
        if (!MemReadable(k0, 0x100) || !MemReadable(k1, 0x100) || !MemReadable(k2, 0x100))
            return false;

        u32 off = DetectHandleOffset(k0, k1, k2);
        if (!off) return false;
        u32 t0 = ReadU32Raw(k0 + off);
        u32 t1 = ReadU32Raw(k1 + off);
        u32 t2 = ReadU32Raw(k2 + off);
        if (t1 != t0 + 1 || t2 != t0 + 2) return false;

        u64 table = ScanForTypeTable(k0, k1, k2, t0, t1, t2);
        if (!table) return false;

        // prove it on a distant sample before trusting 30k reads
        for (size_t probeIdx : { count / 2, count - 1 })
        {
            u64 got = ReadPtr(table + 8ull * (t0 + (u32)probeIdx));
            u64 want = (u64)SafeImageGetClass(probe, probeIdx);
            if (!want || got != want) return false;
        }

        tt.table = table;
        tt.handleOffset = off;
        tt.valid = true;
        return true;
    }

    // one protected call per image, everything else is a plain read
    inline u32 ImageTypeStart(Il2CppImage* img)
    {
        u64 k = (u64)SafeImageGetClass(img, 0);
        TypeTableInfo& tt = TypeTable();
        if (!k || !tt.valid) return 0xFFFFFFFFu;
        return ReadU32Raw(k + tt.handleOffset);
    }

    inline Il2CppClass* FastImageGetClass(Il2CppImage* img, size_t idx, u32 typeStart)
    {
        TypeTableInfo& tt = TypeTable();
        if (!tt.valid || typeStart == 0xFFFFFFFFu) return nullptr;
        u64 k = ReadPtr(tt.table + 8ull * (typeStart + (u32)idx));
        if (!k) return nullptr;
        return (Il2CppClass*)k;
    }

    inline const char* SafeImageGetNameRaw(Il2CppImage* img)
    {
        if (!img || !image_get_name) return nullptr;
        __try { return image_get_name(img); }
        __except (EXCEPTION_EXECUTE_HANDLER) { return nullptr; }
    }

    inline bool SafeMethodName(Il2CppMethod* m, char* buf, size_t cap)
    {
        if (buf && cap) buf[0] = 0;
        if (!m || !method_get_name || !buf || !cap) return false;
        const char* n = nullptr;
        __try { n = method_get_name(m); }
        __except (EXCEPTION_EXECUTE_HANDLER) { n = nullptr; }
        if (!n || !MemReadable((u64)n, 1)) return false;
        size_t i = 0;
        for (; i + 1 < cap; ++i)
        {
            char c = 0;
            if (!SafeRead((u64)n + i, c) || !c)
                break;
            buf[i] = c;
        }
        buf[i] = 0;
        return i > 0;
    }

    inline bool SafeMethodParamCount(Il2CppMethod* m, int* out)
    {
        if (out) *out = 0;
        if (!m || !method_get_param_count) return false;
        __try { *out = method_get_param_count(m); return true; }
        __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
    }

    inline void* SafeDomainGet(bool* ok)
    {
        if (ok) *ok = false;
        if (!domain_get) return nullptr;
        __try { void* d = domain_get(); if (ok) *ok = true; return d; }
        __except (EXCEPTION_EXECUTE_HANDLER) { return nullptr; }
    }

    inline void* SafeThreadAttach(void* domain, bool* ok)
    {
        if (ok) *ok = false;
        if (!domain || !thread_attach) return nullptr;
        __try { void* t = thread_attach(domain); if (ok) *ok = true; return t; }
        __except (EXCEPTION_EXECUTE_HANDLER) { return nullptr; }
    }

    inline Il2CppAssembly** SafeDomainGetAssemblies(void* domain, size_t* count, bool* ok)
    {
        if (count) *count = 0;
        if (ok) *ok = false;
        if (!domain || !domain_get_assemblies) return nullptr;
        __try
        {
            size_t n = 0;
            Il2CppAssembly** a = domain_get_assemblies(domain, &n);
            if (count) *count = n;
            if (ok) *ok = true;
            return a;
        }
        __except (EXCEPTION_EXECUTE_HANDLER) { return nullptr; }
    }

    inline u64 SafeStaticFieldData(Il2CppClass* k, bool* ok)
    {
        if (ok) *ok = false;
        if (!k || !class_get_static_field_data) return 0;
        __try { u64 r = (u64)class_get_static_field_data(k); if (ok) *ok = true; return r; }
        __except (EXCEPTION_EXECUTE_HANDLER) { return 0; }
    }

    inline Il2CppClass* SafeClassGetParent(Il2CppClass* k)
    {
        if (!k || !class_get_parent) return nullptr;
        __try { return class_get_parent(k); }
        __except (EXCEPTION_EXECUTE_HANDLER) { return nullptr; }
    }

    inline Il2CppClass* SafeClassFromName(Il2CppImage* img, const char* ns, const char* name)
    {
        if (!img || !class_from_name) return nullptr;
        __try { return class_from_name(img, ns, name); }
        __except (EXCEPTION_EXECUTE_HANDLER) { return nullptr; }
    }

    inline Il2CppType* SafeClassGetType(Il2CppClass* k)
    {
        if (!k || !class_get_type) return nullptr;
        __try { return class_get_type(k); }
        __except (EXCEPTION_EXECUTE_HANDLER) { return nullptr; }
    }

    inline u64 SafeTypeGetObject(Il2CppType* t)
    {
        if (!t || !type_get_object) return 0;
        __try { return type_get_object(t); }
        __except (EXCEPTION_EXECUTE_HANDLER) { return 0; }
    }

    inline u64 SafeRuntimeInvoke(Il2CppMethod* m, u64 obj, u64* params, u64* exc, bool* ok)
    {
        if (ok) *ok = false;
        if (!m || !runtime_invoke) return 0;
        __try { u64 r = runtime_invoke(m, obj, params, exc); if (ok) *ok = true; return r; }
        __except (EXCEPTION_EXECUTE_HANDLER) { return 0; }
    }

    inline Il2CppClass* FindClass(const char* ns, const char* name)
    {
        if (!domain_get || !domain_get_assemblies || !assembly_get_image || !class_from_name)
            return nullptr;
        void* domain = domain_get();
        if (!domain)
            return nullptr;
        size_t count = 0;
        bool ok = false;
        Il2CppAssembly** asms = SafeDomainGetAssemblies(domain, &count, &ok);
        if (!asms || !count)
            return nullptr;
        for (size_t i = 0; i < count; ++i)
        {
            Il2CppImage* img = SafeAssemblyGetImage(asms[i]);
            if (!img) continue;
            if (Il2CppClass* k = SafeClassFromName(img, ns ? ns : "", name))
                return k;
        }
        return nullptr;
    }

    inline bool FieldIsStatic(Il2CppField* f)
    {
        return f && field_get_flags && (field_get_flags(f) & 0x10) != 0;
    }

    inline u64 FieldOffset(Il2CppField* f)
    {
        return (f && field_get_offset) ? (u64)field_get_offset(f) : 0;
    }

    inline std::string FieldName(Il2CppField* f)
    {
        if (!f) return "";

        // FieldInfo's first qword is the name pointer on this build (the same
        // thing the cheat's Field()/DumpFields() read). Prefer it; the export
        // table aliases several trivial getters and field_get_name can resolve
        // to such an alias.
        u64 p = ReadPtr((u64)f);
        std::string n1 = ReadCStr(p, 160);
        bool printable = !n1.empty();
        for (unsigned char c : n1)
        {
            if (c < 0x20 || c > 0x7E) { printable = false; break; }
        }
        if (printable)
            return n1;

        if (field_get_name)
        {
            const char* n = field_get_name(f);
            if (n && MemReadable((u64)n, 1))
                return ReadCStr((u64)n, 160);
        }
        return "";
    }

    // EAC's metadata protection can fault inside these accessors for a handful
    // of classes.  These helpers are deliberately small and object-free so MSVC
    // accepts __try/__except without C2712, and a fault only skips the class
    // instead of killing the game.
    inline bool SafeClassGetFields(Il2CppClass* k, void** iter, Il2CppField** out)
    {
        *out = nullptr;
        if (!k || !class_get_fields)
            return true;
        __try
        {
            *out = class_get_fields(k, iter);
            return true;
        }
        __except (EXCEPTION_EXECUTE_HANDLER)
        {
            return false;
        }
    }

    inline bool SafeClassGetMethods(Il2CppClass* k, void** iter, Il2CppMethod** out)
    {
        *out = nullptr;
        if (!k || !class_get_methods)
            return true;
        __try
        {
            *out = class_get_methods(k, iter);
            return true;
        }
        __except (EXCEPTION_EXECUTE_HANDLER)
        {
            return false;
        }
    }

    inline bool SafeFieldOffset(Il2CppField* f, size_t* out)
    {
        *out = 0;
        if (!f || !field_get_offset)
            return true;
        __try
        {
            *out = field_get_offset(f);
            return true;
        }
        __except (EXCEPTION_EXECUTE_HANDLER)
        {
            return false;
        }
    }

    inline bool SafeFieldFlags(Il2CppField* f, int* out)
    {
        *out = 0;
        if (!f || !field_get_flags)
            return true;
        __try
        {
            *out = field_get_flags(f);
            return true;
        }
        __except (EXCEPTION_EXECUTE_HANDLER)
        {
            return false;
        }
    }

    inline bool SafeStaticGetValue(Il2CppField* f, void* out)
    {
        if (!f || !field_static_get_value || !out)
            return false;
        __try
        {
            field_static_get_value(f, out);
            return true;
        }
        __except (EXCEPTION_EXECUTE_HANDLER)
        {
            return false;
        }
    }

    inline bool SafeRuntimeClassInit(Il2CppClass* k)
    {
        if (!k || !runtime_class_init)
            return false;
        __try
        {
            runtime_class_init(k);
            return true;
        }
        __except (EXCEPTION_EXECUTE_HANDLER)
        {
            return false;
        }
    }

    // -----------------------------------------------------------------------
    //  live object lookup through UnityEngine.Object.FindObjectsByType
    //  (this is the same route Feed::UnityScan uses and it is the only one
    //   that works on this obfuscated build)
    // -----------------------------------------------------------------------
    inline Il2CppMethod* FindMethodByArgc(Il2CppClass* k, const char* name, int argc)
    {
        if (!k || !class_get_methods || !method_get_name || !method_get_param_count)
            return nullptr;
        void* iter = nullptr;
        while (true)
        {
            Il2CppMethod* m = nullptr;
            if (!SafeClassGetMethods(k, &iter, &m) || !m)
                break;
            if (!MemReadable((u64)m, 0x20))
                continue;
            int pc = 0;
            if (!SafeMethodParamCount(m, &pc) || pc != argc)
                continue;
            char buf[192]{};
            if (SafeMethodName(m, buf, sizeof(buf)) && StrEq(buf, name))
                return m;
        }
        return nullptr;
    }

    inline Il2CppClass* ObjectClass()
    {
        static Il2CppClass* k = nullptr;
        if (!k) k = FindClass("UnityEngine", "Object");
        return k;
    }

    // returns Il2CppArray* and sets outLen; data starts at +0x20, length at +0x18
    // `why` (optional) receives a short reason on failure so the caller can log it
    inline u64 FindObjectsOfType(Il2CppClass* target, u32* outLen, const char** why = nullptr,
                                 int* overloadArgc = nullptr)
    {
        if (outLen) *outLen = 0;
        if (why) *why = "";
        if (overloadArgc) *overloadArgc = 0;

        if (!target) { if (why) *why = "target class is null"; return 0; }
        if (!runtime_invoke || !type_get_object || !class_get_type)
        {
            if (why) *why = "il2cpp_runtime_invoke / il2cpp_type_get_object / il2cpp_class_get_type export missing";
            return 0;
        }

        Il2CppClass* objK = ObjectClass();
        if (!objK) { if (why) *why = "UnityEngine.Object class not found"; return 0; }

        // make sure the whole ancestor chain is initialized (Unity checks BaseType)
        Il2CppClass* cur = target;
        for (int depth = 0; depth < 24 && cur; ++depth)
        {
            if (runtime_class_init) SafeRuntimeClassInit(cur);
            if (cur == objK) break;
            Il2CppClass* p = SafeClassGetParent(cur);
            if (!p || p == cur) break;
            cur = p;
        }

        Il2CppType* ptype = SafeClassGetType(target);
        if (!ptype) { if (why) *why = "il2cpp_class_get_type returned null"; return 0; }
        u64 typeObj = SafeTypeGetObject(ptype);
        if (!typeObj) { if (why) *why = "il2cpp_type_get_object returned null"; return 0; }

        static Il2CppMethod* m3 = nullptr;
        static Il2CppMethod* m2 = nullptr;
        static Il2CppMethod* m1 = nullptr;
        if (!m3 && !m2 && !m1)
        {
            m3 = FindMethodByArgc(objK, "FindObjectsByType", 3);
            m2 = FindMethodByArgc(objK, "FindObjectsOfType", 2);
            m1 = FindMethodByArgc(objK, "FindObjectsOfType", 1);
        }

        Il2CppMethod* m = m3 ? m3 : (m2 ? m2 : m1);
        int argc = m3 ? 3 : (m2 ? 2 : 1);
        if (!m)
        {
            if (why) *why = "no FindObjectsByType(3)/FindObjectsOfType(2/1) on UnityEngine.Object";
            return 0;
        }
        if (overloadArgc) *overloadArgc = argc;

        u32 v0 = 0, v1 = 0;
        u64 params[3] = { typeObj, 0, 0 };
        if (argc >= 2) params[1] = (u64)&v0;
        if (argc >= 3) params[2] = (u64)&v1;

        u64 exc = 0;
        bool invokeOk = false;
        u64 arr = SafeRuntimeInvoke(m, 0, params, &exc, &invokeOk);
        if (!invokeOk) { if (why) *why = "il2cpp_runtime_invoke faulted"; return 0; }
        if (exc) { if (why) *why = "managed exception thrown by the invoke"; return 0; }
        if (!arr) { if (why) *why = "invoke returned null array"; return 0; }
        if (!MemReadable(arr, 0x28)) { if (why) *why = "returned array is not readable"; return 0; }

        u32 len = ReadU32(arr + 0x18);
        if (len > 400000) { if (why) *why = "returned array length is implausible"; return 0; }
        if (outLen) *outLen = len;
        return arr;
    }

    inline u64 ObjClass(u64 obj)
    {
        return obj ? ReadPtr(obj) : 0;
    }
}

// ---------------------------------------------------------------------------
//  decryptors
//
//  The chains are no longer typed in by hand.  tools/reverse.py recovers the
//  real cipher block from GameAssembly.dll (symbolic execution of the machine
//  code) and emits src/generated/Decryptors.generated.h.  For every routine the
//  generator also stores the RVA and a FNV-1a hash of the first 64 bytes of the
//  block, so VerifyGeneratedDecryptors() can prove at dump time that the game
//  binary still contains exactly the code the chains were derived from.
//
//  If Facepunch ships a new build the verification fails loudly and the dumper
//  tells you to re-run:  py tools/reverse.py
// ---------------------------------------------------------------------------
inline u32 Rol32(u32 v, u32 n) { n &= 31; return n ? (v << n) | (v >> (32 - n)) : v; }
inline u32 Ror32(u32 v, u32 n) { n &= 31; return n ? (v >> n) | (v << (32 - n)) : v; }

inline bool LoadEncryptedWords(u64 a1, u32 w[2])
{
    if (!MemReadable(a1 + 0x10, 1)) return false;
    u8 flag = 0;
    SafeRead(a1 + 0x10, flag);
    if (!flag) return false;
    u64 raw = ReadU64(a1 + 0x18);
    w[0] = (u32)(raw & 0xFFFFFFFF);
    w[1] = (u32)(raw >> 32);
    return true;
}

#include "generated/Decryptors.generated.h"

// Curated gameplay offsets, regenerated from a live dump by tools/analyze_dump.py.
// Absent until the first dump has been post-processed - the include is optional.
#if __has_include("generated/Offsets.generated.h")
#include "generated/Offsets.generated.h"
#endif

inline u64 ClientEntitiesDecrypt(u64 a1)             { return generated::ClientEntitiesDecrypt(a1); }
inline u64 EntityListDecrypt(u64 a1)                 { return generated::EntityListDecrypt(a1); }
inline u64 PlayerEyesDecrypt(u64 a1)                 { return generated::PlayerEyesDecrypt(a1); }
inline u64 PlayerInventoryDecrypt(u64 a1)            { return generated::PlayerInventoryDecrypt(a1); }
inline u64 ClActiveItemDecrypt(u64 raw)              { return generated::ClActiveItemDecrypt(raw); }
inline u64 UserIDDecrypt(u64 raw)                    { return generated::UserIDDecrypt(raw); }
inline u64 PlayerWalkMovementBodyDecrypt(u64 a1)     { return generated::PlayerWalkMovementBody(a1); }
inline u64 PlayerWalkMovementCapsuleDecrypt(u64 a1)  { return generated::PlayerWalkMovementCapsule(a1); }
inline u64 BasePlayerCapsuleColliderDecrypt(u64 a1)  { return generated::BasePlayerCapsuleCollider(a1); }

inline u32 Fnv1a32(const void* data, size_t n)
{
    u32 h = 0x811C9DC5u;
    const u8* p = (const u8*)data;
    for (size_t i = 0; i < n; ++i)
    {
        h ^= p[i];
        h *= 0x01000193u;
    }
    return h;
}

// true = binary still matches every generated chain.
// report receives one line per decryptor; mismatches are marked [!].
inline bool VerifyGeneratedDecryptors(u64 gameAssembly, std::string* report)
{
    struct Entry { const char* name; u64 blockRva; u32 hash; };
    static const Entry kEntries[] = {
        { "ClientEntitiesDecrypt",        generated::kClientEntitiesDecryptBlockRva,       generated::kClientEntitiesDecryptBlockHash },
        { "EntityListDecrypt",            generated::kEntityListDecryptBlockRva,           generated::kEntityListDecryptBlockHash },
        { "PlayerEyesDecrypt",            generated::kPlayerEyesDecryptBlockRva,           generated::kPlayerEyesDecryptBlockHash },
        { "PlayerInventoryDecrypt",       generated::kPlayerInventoryDecryptBlockRva,      generated::kPlayerInventoryDecryptBlockHash },
        { "ClActiveItemDecrypt",          generated::kClActiveItemDecryptBlockRva,         generated::kClActiveItemDecryptBlockHash },
        { "UserIDDecrypt",                generated::kUserIDDecryptBlockRva,               generated::kUserIDDecryptBlockHash },
        { "PlayerWalkMovementBody",       generated::kPlayerWalkMovementBodyBlockRva,      generated::kPlayerWalkMovementBodyBlockHash },
        { "PlayerWalkMovementCapsule",    generated::kPlayerWalkMovementCapsuleBlockRva,   generated::kPlayerWalkMovementCapsuleBlockHash },
        { "BasePlayerCapsuleCollider",    generated::kBasePlayerCapsuleColliderBlockRva,   generated::kBasePlayerCapsuleColliderBlockHash },
    };

    if (report) report->clear();
    if (!gameAssembly)
        return false;

    bool all = true;
    for (const auto& e : kEntries)
    {
        u64 addr = gameAssembly + e.blockRva;
        char line[256]{};
        if (!MemReadable(addr, 64))
        {
            sprintf_s(line, sizeof(line), "  [!] %-30s block 0x%llX unreadable",
                e.name, (unsigned long long)e.blockRva);
            all = false;
        }
        else
        {
            u32 h = Fnv1a32((const void*)addr, 64);
            bool ok = (h == e.hash);
            sprintf_s(line, sizeof(line), "  [%s] %-30s block 0x%llX hash 0x%08X",
                ok ? " OK " : "!!!", e.name, (unsigned long long)e.blockRva, h);
            if (!ok)
                all = false;
        }
        if (report)
        {
            *report += line;
            *report += "\n";
        }
    }
    return all;
}

// -- gchandle resolution (same rules as the runtime's chunked table) ---------
inline u64 SafeGcHandleResolve(u64 value)
{
    if (!value) return 0;
    u64 chunk = value & ~0x1FFFULL;
    if (!MemReadable(chunk, 0x28)) return 0;
    u8 type = 0; SafeRead(chunk + 0x20, type);
    if (type >= 4) return 0;
    if (value < chunk + 0x28) return 0;
    u64 index = (value - chunk - 0x28) >> 3;
    u32 count = ReadU32(chunk + 0x1C);
    if (index >= count) return 0;
    u64 bitmap = ReadU64(chunk + 0x10);
    if (!bitmap || !MemReadable(bitmap + (index >> 5) * 4, 4)) return 0;
    u32 word = ReadU32(bitmap + (index >> 5) * 4);
    if ((word & (1u << (index & 0x1F))) == 0) return 0;
    u64 slot = chunk + 0x28 + index * 8;
    u64 raw = ReadU64(slot);
    if (type > 1) return raw;
    u64 inv = ~raw;
    return inv == (u64)-1 ? 0 : inv;
}

inline u64 ResolveHandle(u64 value)
{
    if (!value) return 0;
    u64 r = SafeGcHandleResolve(value);
    if (r && MemReadable(r, 0x10)) return r;
    if (value >= 0x100000000ULL && MemReadable(value, 0x20)) return value;
    return 0;
}

inline bool LooksLikeKlass(u64 k)
{
    if (!k || !MemReadable(k, 0x100)) return false;
    std::string name = il2::KlassName((void*)k);
    return !name.empty();
}

inline bool LooksLikeEntityList(u64 p, u32* outCount = nullptr)
{
    if (!p || !MemReadable(p, 0x30)) return false;
    u32 count = ReadU32(p + 0x18);
    u64 items = ReadPtr(p + 0x20);
    if (count > 400000 || !items || !MemReadable(items, 8)) return false;
    if (outCount) *outCount = count;
    return true;
}

inline bool LooksLikeEntityArray(u64 p, u32* outCount = nullptr)
{
    if (!p || !MemReadable(p, 0x30)) return false;
    u32 len = ReadU32(p + 0x18);
    u64 data = p + 0x20;
    if (!len || len > 400000 || !MemReadable(data, 8)) return false;
    u64 first = ReadPtr(data);
    if (!first || !LooksLikeKlass(ReadPtr(first))) return false;
    if (outCount) *outCount = len;
    return true;
}
