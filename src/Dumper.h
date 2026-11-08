#pragma once

#include "Il2Cpp.h"
#include "generated/NameOverrides.generated.h"
#include "generated/TypeInfoTokens.generated.h"
#include "generated/ReversOffsets.generated.h"
#include "StaticResolver.h"
#include <cstdarg>
#include <ctime>
#include <fstream>
#include <sstream>
#include <set>
#include <map>

// ---------------------------------------------------------------------------
//  logging - dedicated console window + raw WriteFile log
//
//  We do NOT use CRT stdio here.  Under the game process the CRT stream buffer
//  did not reach the disk (log stayed 0 bytes while the worker was running), so
//  every line is written straight through WriteFile and flushed immediately.
//  The exact same line goes to:
//    - the allocated console window (so the user sees it live)
//    - Rust-Offset-Dumper_log.txt (flush every line)
//    - OutputDebugStringA (DbgView)
// ---------------------------------------------------------------------------
inline CRITICAL_SECTION g_logCs;
inline bool g_logCsInit = false;
inline HANDLE g_logFile = INVALID_HANDLE_VALUE;
inline HANDLE g_conOut = INVALID_HANDLE_VALUE;
inline bool g_conOwned = false;
inline std::string g_outDir;
inline DWORD g_dumpStartTick = 0;
inline DWORD g_lastFileFlush = 0;
inline u32 g_linesSinceFlush = 0;

inline void LogTimestamp(char* out, size_t outSize)
{
    SYSTEMTIME st{};
    GetLocalTime(&st);
    sprintf_s(out, outSize, "%02u:%02u:%02u.%03u",
        st.wHour, st.wMinute, st.wSecond, st.wMilliseconds);
}

inline void Log(const char* fmt, ...); // defined below; used by the hash table loader

// ---------------------------------------------------------------------------
//  EAC hash -> name table
//
//  The metadata obfuscator replaces identifiers with a 40-hex token.  This was
//  tested against 1.25M unique strings from the live GameAssembly.dll and
//  global-metadata.dat, and against every plausible textual form of two known
//  identifiers (namespace/assembly prefixes, get_/m_ prefixes, UTF-8/16/32,
//  sha1/ripemd160/blake2b/sha2-*/sha3): zero matches.  It is a keyed one-way
//  hash - there is no "reverse" and no dictionary that can crack it.
//
//  Therefore the only way to get a readable name back is to *record* one:
//    - seeds from the generated table (community reference for this build),
//    - plus <outDir>\Rust-Offset-Dumper_hash_names.txt, which the user can edit and
//      which the dumper rewrites every run with all unresolved hashes.
//  A name is attached to the hash itself, so one entry fixes class names, field
//  names and nested type names (%hash.Phrase) at once.
// ---------------------------------------------------------------------------
inline std::map<std::string, std::string> g_hashNames;    // 40hex -> readable
inline std::map<std::string, std::string> g_hashContext;  // 40hex -> first use
inline std::map<std::string, std::string> g_hashNotes;    // 40hex -> user note
inline size_t g_hashHits = 0;
inline size_t g_hashMisses = 0;

inline bool IsHexChar(char c)
{
    return (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f') || (c >= 'A' && c <= 'F');
}

// True when a full 40-hex run starts at s[i] and is not part of a longer run.
inline bool HashTokenAt(const std::string& s, size_t i)
{
    if (i + 40 > s.size()) return false;
    for (size_t k = 0; k < 40; ++k)
        if (!IsHexChar(s[i + k])) return false;
    if (i > 0 && IsHexChar(s[i - 1])) return false;
    if (i + 40 < s.size() && IsHexChar(s[i + 40])) return false;
    return true;
}

inline std::string LowerHash(const std::string& h)
{
    std::string o = h;
    for (char& c : o)
        if (c >= 'A' && c <= 'F') c = (char)(c - 'A' + 'a');
    return o;
}

inline void RememberHash(const std::string& hash, const std::string& ctx)
{
    ++g_hashMisses;
    if (g_hashContext.find(hash) == g_hashContext.end())
        g_hashContext[hash] = ctx;
}

// Replace %<40hex> / _<40hex> tokens with known names and leave unknown tokens
// untouched.  Used for class names, field names and nested type names.
inline std::string ResolveHashTokens(const std::string& s, const std::string& ctx)
{
    std::string out;
    out.reserve(s.size());
    size_t i = 0;
    while (i < s.size())
    {
        if ((s[i] == '%' || s[i] == '_') && HashTokenAt(s, i + 1))
        {
            const std::string h = LowerHash(s.substr(i + 1, 40));
            auto it = g_hashNames.find(h);
            if (it != g_hashNames.end())
            {
                ++g_hashHits;
                out += it->second;
            }
            else
            {
                RememberHash(h, ctx);
                out.append(s, i, 41);
            }
            i += 41;
            continue;
        }
        if (HashTokenAt(s, i))
        {
            const std::string h = LowerHash(s.substr(i, 40));
            auto it = g_hashNames.find(h);
            if (it != g_hashNames.end())
            {
                ++g_hashHits;
                out += it->second;
            }
            else
            {
                RememberHash(h, ctx);
                out.append(s, i, 40);
            }
            i += 40;
            continue;
        }
        out += s[i++];
    }
    return out;
}

inline std::string DeobfuscateKlassName(const std::string& raw)
{
    return ResolveHashTokens(raw, "class name");
}

inline bool FieldTypeMatches(const char* expected, const std::string& actual)
{
    if (!expected || !expected[0] || actual.empty())
        return true;
    std::string e(expected), a(actual);
    auto lower = [](std::string s)
    {
        for (char& c : s) c = (char)tolower((unsigned char)c);
        return s;
    };
    auto tail = [&](std::string s)
    {
        size_t p = s.find_last_of('.');
        return lower(p == std::string::npos ? s : s.substr(p + 1));
    };
    std::string at = tail(a);
    // a hashed type name carries no usable information
    if (!at.empty() && at[0] == '%')
        return true;
    // metadata often declares a base type (System.Object) for reference fields
    if (at == "object")
        return true;
    static const struct { const char* a; const char* b; } alias[] = {
        { "float", "single" }, { "int", "int32" }, { "uint", "uint32" },
        { "long", "int64" }, { "ulong", "uint64" }, { "short", "int16" },
        { "ushort", "uint16" }, { "bool", "boolean" }, { "string", "string" },
    };
    std::string et = tail(e);
    if (et == at) return true;
    for (const auto& al : alias)
    {
        std::string x = al.a, y = al.b;
        if ((et == x && at == y) || (et == y && at == x))
            return true;
    }
    return et.find(at) != std::string::npos || at.find(et) != std::string::npos;
}

inline std::string DeobfuscateFieldName(const std::string& klass,
                                        const std::string& raw, u32 offset,
                                        const std::string& fieldType = std::string())
{
    if (raw.size() >= 2 && raw[0] == '%')
    {
        // Offset-proven names come first.  revers/rev_binary.py tied the name to
        // this exact (class, offset) slot, while a hash table maps one token to
        // one name everywhere - and the same token can be reused by a different
        // field of the same class (e.g. BasePlayer+0x2F0 vs +0x6F8).  The proof
        // is per slot, so it wins.
        if (const char* n = revers_offsets::NameFor(klass.c_str(), offset))
            return n;

        // Community evidence: exact (class, offset, type) slot.
        for (const auto& f : name_overrides::fields)
            if (f.offset == offset && klass == f.klass &&
                FieldTypeMatches(f.expected_type, fieldType))
                return f.name;
    }
    char ctx[160];
    sprintf_s(ctx, sizeof(ctx), "field %s+0x%X", klass.c_str(), offset);
    std::string resolved = ResolveHashTokens(raw, ctx);
    if (resolved.empty() || staticscan::HashLikeName(resolved))
    {
        if (const char* n = revers_offsets::NameFor(klass.c_str(), offset))
            return n;
    }
    return resolved;
}

inline std::string HashNameTablePath()
{
    return g_outDir.empty() ? std::string() : g_outDir + "\\Rust-Offset-Dumper_hash_names.txt";
}

// Seed from the generated table, then merge the user-editable file.  File
// entries override generated ones, so a hand-written name always wins.
inline void LoadHashNames()
{
    g_hashNames.clear();
    g_hashContext.clear();
    g_hashNotes.clear();
    g_hashHits = 0;
    g_hashMisses = 0;
    for (const auto& h : name_overrides::hashes)
        g_hashNames[LowerHash(h.hash)] = h.name;
    for (const auto& h : name_overrides::classes)
        g_hashNames[LowerHash(h.hash)] = h.name;

    const std::string path = HashNameTablePath();
    if (path.empty())
    {
        Log("[HASH] no output dir - %zu built-in names only", g_hashNames.size());
        return;
    }
    std::ifstream f(path.c_str());
    if (!f)
    {
        Log("[HASH] no table yet (%s) - will create it after this run", path.c_str());
        return;
    }

    size_t named = 0, unresolved = 0, bad = 0, lineNo = 0;
    std::string line;
    while (std::getline(f, line))
    {
        ++lineNo;
        if (!line.empty() && line.back() == '\r') line.pop_back();
        size_t a = line.find_first_not_of(" \t");
        if (a == std::string::npos || line[a] == '#') continue;
        size_t eq = line.find('=');
        if (eq == std::string::npos)
        {
            ++bad;
            Log("[HASH][!] table line %zu has no '=' - ignored: %s", lineNo, line.c_str());
            continue;
        }
        std::string key = line.substr(a, eq - a);
        while (!key.empty() && (key.back() == ' ' || key.back() == '\t')) key.pop_back();
        if (!key.empty() && (key[0] == '%' || key[0] == '_')) key.erase(key.begin());
        if (key.size() != 40 || !HashTokenAt(key + " ", 0))
        {
            ++bad;
            Log("[HASH][!] table line %zu has an invalid hash - ignored: %s", lineNo, line.c_str());
            continue;
        }
        std::string rest = line.substr(eq + 1);
        std::string note;
        size_t hashPos = rest.find('#');
        if (hashPos != std::string::npos)
        {
            note = rest.substr(hashPos + 1);
            rest = rest.substr(0, hashPos);
        }
        size_t b = rest.find_first_not_of(" \t;");
        size_t e = rest.find_last_not_of(" \t;");
        std::string name = (b == std::string::npos) ? std::string()
                                                    : rest.substr(b, e - b + 1);
        const std::string h = LowerHash(key);
        if (name.empty())
        {
            ++unresolved;
            if (!note.empty()) g_hashNotes[h] = note;
        }
        else
        {
            g_hashNames[h] = name;
            ++named;
        }
    }
    const size_t builtin = sizeof(name_overrides::classes) / sizeof(name_overrides::classes[0])
                         + sizeof(name_overrides::hashes) / sizeof(name_overrides::hashes[0]);
    Log("[HASH] table loaded: %zu built-in names + %zu file names, %zu unresolved line(s), %zu malformed line(s)",
        builtin, named, unresolved, bad);
}

// Called once after enumeration: writes every known name plus a template line
// for each hash the dump met but could not name, with the slot it was seen in.
inline void WriteHashNameTable(const std::string& path)
{
    std::ofstream f(path, std::ios::binary);
    if (!f)
    {
        Log("[WRITE][!] cannot write hash table %s", path.c_str());
        return;
    }
    f << "# Rust-Offset-Dumper hash -> name table\n";
    f << "# The 40-hex token is a keyed one-way hash of the original identifier:\n";
    f << "#   it cannot be reversed (verified against 1.25M strings and every\n";
    f << "#   plausible template).  Fill names in after '=' and re-run: the dumper\n";
    f << "#   applies them to class, field and nested type names automatically.\n";
    f << "# Format:  %<40 hex> = Name   # optional note\n";
    f << "#\n";
    f << "# resolved: " << g_hashNames.size() << "\n\n";

    for (const auto& kv : g_hashNames)
        f << "%" << kv.first << " = " << kv.second << "\n";

    f << "\n# unresolved during this run: " << g_hashContext.size() << "\n";
    f << "# (hash = empty name; a note shows where it was seen)\n\n";
    for (const auto& kv : g_hashContext)
    {
        if (g_hashNames.find(kv.first) != g_hashNames.end())
            continue;
        auto note = g_hashNotes.find(kv.first);
        f << "%" << kv.first << " = ; # "
          << (note != g_hashNotes.end() ? note->second : kv.second) << "\n";
    }
    Log("[WRITE] hash table: %s (%zu named, %zu unresolved)",
        path.c_str(), g_hashNames.size(), g_hashContext.size());
}

inline BOOL WINAPI ConsoleCtrlHandlerRoutine(DWORD)
{
    return TRUE; // swallow every console event - closing the console must not kill the game
}

inline void OpenConsole()
{
    if (GetConsoleWindow())
    {
        g_conOut = GetStdHandle(STD_OUTPUT_HANDLE);
        return;
    }

    if (!AllocConsole())
        return;

    g_conOwned = true;
    SetConsoleTitleA("Rust-Offset-Dumper - live IL2CPP dump");

    g_conOut = CreateFileA("CONOUT$", GENERIC_READ | GENERIC_WRITE,
        FILE_SHARE_READ | FILE_SHARE_WRITE, nullptr, OPEN_EXISTING, 0, nullptr);
    if (g_conOut == INVALID_HANDLE_VALUE)
        g_conOut = GetStdHandle(STD_OUTPUT_HANDLE);

    // keep the game alive if the user closes / Ctrl+C the console
    SetConsoleCtrlHandler(ConsoleCtrlHandlerRoutine, TRUE);

    CONSOLE_SCREEN_BUFFER_INFOEX bi{};
    bi.cbSize = sizeof(bi);
    if (g_conOut != INVALID_HANDLE_VALUE && GetConsoleScreenBufferInfoEx(g_conOut, &bi))
    {
        bi.dwSize.X = 160;
        bi.dwSize.Y = 4000;
        SetConsoleScreenBufferSize(g_conOut, bi.dwSize);
    }

    // QuickEdit is a trap: clicking/selecting text in the console blocks every
    // WriteFile to it, which freezes the dumper thread (and can stall the game).
    HANDLE conIn = GetStdHandle(STD_INPUT_HANDLE);
    DWORD inMode = 0;
    if (conIn != INVALID_HANDLE_VALUE && GetConsoleMode(conIn, &inMode))
        SetConsoleMode(conIn, (inMode & ~ENABLE_QUICK_EDIT_MODE) | ENABLE_EXTENDED_FLAGS);

    // make stdio writes also reach the console (some code paths use printf)
    FILE* f = nullptr;
    freopen_s(&f, "CONOUT$", "w", stdout);
    freopen_s(&f, "CONOUT$", "w", stderr);
}

inline void LogInit(const std::string& dir)
{
    g_outDir = dir;
    CreateDirectoryA(dir.c_str(), nullptr);

    if (!g_logCsInit)
    {
        InitializeCriticalSection(&g_logCs);
        g_logCsInit = true;
    }

    OpenConsole();
    g_dumpStartTick = GetTickCount();

    std::string path = dir + "\\Rust-Offset-Dumper_log.txt";
    g_logFile = CreateFileA(path.c_str(), GENERIC_WRITE,
        FILE_SHARE_READ | FILE_SHARE_WRITE, nullptr,
        CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
}

inline void Log(const char* fmt, ...)
{
    char msg[8192]{};
    va_list ap;
    va_start(ap, fmt);
    vsnprintf_s(msg, sizeof(msg), _TRUNCATE, fmt, ap);
    va_end(ap);

    char ts[32]{};
    LogTimestamp(ts, sizeof(ts));

    char line[8448]{};
    int n = sprintf_s(line, sizeof(line), "[%s][T%05lu][%6lu ms] %s\r\n",
        ts, (unsigned long)GetCurrentThreadId(),
        (unsigned long)(g_dumpStartTick ? (GetTickCount() - g_dumpStartTick) : 0),
        msg);
    if (n <= 0)
        return;
    size_t len = (size_t)n;
    if (len >= sizeof(line))
        len = sizeof(line) - 1;

    if (g_logCsInit) EnterCriticalSection(&g_logCs);

    if (g_conOut != INVALID_HANDLE_VALUE)
    {
        DWORD wrote = 0;
        WriteFile(g_conOut, line, (DWORD)len, &wrote, nullptr);
    }

    if (g_logFile != INVALID_HANDLE_VALUE)
    {
        DWORD wrote = 0;
        WriteFile(g_logFile, line, (DWORD)len, &wrote, nullptr);
        g_linesSinceFlush++;
        DWORD now = GetTickCount();
        if (g_linesSinceFlush >= 4096 || (now - g_lastFileFlush) >= 2000)
        {
            FlushFileBuffers(g_logFile);
            g_lastFileFlush = now;
            g_linesSinceFlush = 0;
        }
    }

    if (IsDebuggerPresent())
        OutputDebugStringA(line);

    if (g_logCsInit) LeaveCriticalSection(&g_logCs);
}

inline void LogHexDump(const char* label, u64 addr, u32 bytes)
{
    if (!addr || !MemReadable(addr, bytes))
    {
        Log("  %s @0x%llX <unreadable>", label, (unsigned long long)addr);
        return;
    }
    Log("  %s @0x%llX (%u bytes):", label, (unsigned long long)addr, bytes);
    for (u32 i = 0; i < bytes; i += 16)
    {
        char row[128]{};
        int pos = sprintf_s(row, sizeof(row), "    +0x%03X:", i);
        for (u32 j = 0; j < 16 && i + j < bytes; ++j)
        {
            if (pos < (int)sizeof(row) - 4)
                pos += sprintf_s(row + pos, sizeof(row) - pos, " %02X", *(u8*)(addr + i + j));
        }
        Log("%s", row);
    }
}

inline void LogExportStatus()
{
    struct Entry { const char* name; bool required; };
    const Entry entries[] = {
        { "il2cpp_domain_get", true },
        { "il2cpp_thread_attach", false },
        { "il2cpp_domain_get_assemblies", true },
        { "il2cpp_assembly_get_image", true },
        { "il2cpp_image_get_class_count", true },
        { "il2cpp_image_get_class", true },
        { "il2cpp_image_get_name", false },
        { "il2cpp_class_get_name", true },
        { "il2cpp_class_get_namespace", false },
        { "il2cpp_class_get_parent", false },
        { "il2cpp_class_get_fields", true },
        { "il2cpp_class_get_methods", false },
        { "il2cpp_class_get_static_field_data", false },
        { "il2cpp_class_get_type", false },
        { "il2cpp_class_from_name", false },
        { "il2cpp_field_get_name", false },
        { "il2cpp_field_get_offset", true },
        { "il2cpp_field_get_flags", false },
        { "il2cpp_field_get_type", false },
        { "il2cpp_field_static_get_value", false },
        { "il2cpp_method_get_name", false },
        { "il2cpp_method_get_param_count", false },
        { "il2cpp_method_get_param_name", false },
        { "il2cpp_method_get_param", false },
        { "il2cpp_type_get_name", false },
        { "il2cpp_type_get_object", false },
        { "il2cpp_runtime_class_init", false },
        { "il2cpp_gchandle_get_target", false },
        { "il2cpp_runtime_invoke", false },
        { "il2cpp_object_new", false },
    };
    const size_t entryCount = sizeof(entries) / sizeof(entries[0]);

    u64 addrs[sizeof(entries) / sizeof(entries[0])]{};
    const char* fwd[sizeof(entries) / sizeof(entries[0])]{};

    Log("[EXPORTS] GameAssembly export scan (module=0x%llX):",
        (unsigned long long)il2::module);
    for (size_t i = 0; i < entryCount; ++i)
        addrs[i] = GetExportEx(il2::module, entries[i].name, &fwd[i]);

    int found = 0, missing = 0, aliased = 0, outOfRange = 0;
    for (size_t i = 0; i < entryCount; ++i)
    {
        const Entry& e = entries[i];
        if (!addrs[i])
        {
            missing++;
            if (fwd[i])
                Log("  [FWD ] %-38s -> forwarder '%s'", e.name, fwd[i]);
            else
                Log("  [MISS] %-38s   (%s)", e.name, e.required ? "REQUIRED" : "optional");
            continue;
        }

        found++;

        // ICF folds identical tiny accessors (e.g. "return *(void**)rcx")
        // into one address. Report it instead of confusing the reader.
        const char* aliasOf = nullptr;
        for (size_t j = 0; j < i; ++j)
            if (addrs[j] == addrs[i]) { aliasOf = entries[j].name; break; }
        if (aliasOf) aliased++;

        bool inRange = false;
        if (il2::module)
        {
            u64 size = GetPeSizeOfImage(il2::module);
            inRange = addrs[i] >= il2::module && (!size || addrs[i] < il2::module + size);
        }
        if (!inRange) outOfRange++;

        Log("  [ OK ] %-38s = 0x%llX  (+0x%llX)%s%s%s",
            e.name, (unsigned long long)addrs[i],
            (unsigned long long)(addrs[i] - il2::module),
            aliasOf ? "  [shared/ICF body of " : "",
            aliasOf ? aliasOf : "",
            aliasOf ? "]" : "");
    }
    Log("[EXPORTS] found=%d missing=%d aliased=%d outside-module=%d",
        found, missing, aliased, outOfRange);
}

inline void LogFileWritten(const std::string& path)
{
    WIN32_FILE_ATTRIBUTE_DATA fad{};
    if (GetFileAttributesExA(path.c_str(), GetFileExInfoStandard, &fad))
    {
        u64 size = ((u64)fad.nFileSizeHigh << 32) | fad.nFileSizeLow;
        Log("[FILE] %s  (%llu bytes)", path.c_str(), (unsigned long long)size);
    }
    else
    {
        Log("[FILE][!] %s  NOT WRITTEN (err=%lu)", path.c_str(), GetLastError());
    }
}

inline std::string TimestampNow();

inline void LogClose()
{
    if (g_logFile != INVALID_HANDLE_VALUE)
    {
        FlushFileBuffers(g_logFile);
        CloseHandle(g_logFile);
        g_logFile = INVALID_HANDLE_VALUE;
    }
    if (g_conOwned && g_conOut != INVALID_HANDLE_VALUE)
    {
        CloseHandle(g_conOut);
        g_conOut = INVALID_HANDLE_VALUE;
    }
}

// ---------------------------------------------------------------------------
//  data model
// ---------------------------------------------------------------------------
struct FieldRow
{
    void* field = nullptr;
    std::string name;
    std::string rawName;   // metadata name before hash resolution (%hash when obfuscated)
    u32 offset = 0;
    u32 flags = 0;
    std::string typeName;
    // where the written offset came from (see staticscan::Evidence)
    u8  evidence = 0;      // 0 none, 1 live, 2 table-verified, 3 table-filled
};

struct MethodRow
{
    void* method = nullptr;
    std::string name;
    int argc = 0;
    u64 code = 0;
    u64 rva = 0;
};

struct ClassRow
{
    void* klass = nullptr;
    std::string ns;
    std::string name;
    void* parent = nullptr;
    u64 staticData = 0;
    bool target = false;
    std::vector<FieldRow> fields;
    std::vector<MethodRow> methods;
    // verified .rdata field-offset table (revers/rev_binary.py equivalent)
    bool tableFound = false;
    u32  tableRva = 0;
    int  tableAnchors = 0;   // fields whose live offset was used to pin the table
    int  tableVerified = 0;  // live offsets confirmed by that table
    int  tableFilled = 0;    // slots recovered from the table
};

struct DumpResult
{
    u64 gameAssembly = 0;
    u64 imageSize = 0;
    std::vector<ClassRow> classes;
    std::unordered_set<u64> klassSet;
    std::unordered_map<u64, std::vector<u32>> typeInfoRvas;
    // encoded lazy TypeInfo usage token -> slots holding it
    std::unordered_map<u32, std::vector<u32>> typeInfoTokenRvas;
    std::string timestamp;
};

// Token values we are willing to record during the data-section scan.  Kept
// small so the scan never turns into a generic "collect every odd qword" pass.
inline const std::unordered_set<u32>& ExpectedTypeInfoTokens()
{
    static const std::unordered_set<u32> set = [] {
        std::unordered_set<u32> s;
        for (const auto& t : typeinfo_tokens::tokens)
            s.insert(0x20000000u | (t.index << 1) | 1u);
        return s;
    }();
    return set;
}

inline bool IsCppKeyword(const std::string& s)
{
    static const std::set<std::string> kw = {
        "alignas","alignof","and","and_eq","asm","auto","bitand","bitor","bool",
        "break","case","catch","char","char8_t","char16_t","char32_t","class",
        "compl","concept","const","consteval","constexpr","constinit","const_cast",
        "continue","co_await","co_return","co_yield","decltype","default","delete",
        "do","double","dynamic_cast","else","enum","explicit","export","extern",
        "false","float","for","friend","goto","if","inline","int","long","mutable",
        "namespace","new","noexcept","not","not_eq","nullptr","operator","or","or_eq",
        "private","protected","public","register","reinterpret_cast","requires",
        "return","short","signed","sizeof","static","static_assert","static_cast",
        "struct","switch","template","this","thread_local","throw","true","try",
        "typedef","typeid","typename","union","unsigned","using","virtual","void",
        "volatile","wchar_t","while","xor","xor_eq"
    };
    return kw.count(s) != 0;
}

inline std::string SanitizeIdent(const std::string& in)
{
    std::string out;
    for (char c : in)
    {
        if ((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == '_')
            out += c;
        else
            out += '_';
    }
    if (out.empty()) out = "unnamed";
    if (out[0] >= '0' && out[0] <= '9') out = "_" + out;
    if (IsCppKeyword(out)) out = "_" + out;
    return out;
}

inline std::string Qualified(const ClassRow& c)
{
    return c.ns.empty() ? c.name : (c.ns + "::" + c.name);
}

inline const char* TargetMatchReason(const std::string& name)
{
    static const std::set<std::string> exact = {
        "BaseNetworkable","BaseNetworkable.EntityRealm","BasePlayer","BaseCombatEntity",
        "BaseEntity","BaseProjectile","BaseMelee","AttackEntity","PlayerEyes","PlayerModel",
        "PlayerWalkMovement","PlayerTick","PlayerInventory","PlayerInput","InputState",
        "InputMessage","ModelState","Item","ItemContainer","HeldEntity","ViewModel",
        "Projectile","ProjectileShoot","PlayerProjectileAttack","PlayerAttack","Attack",
        "SkinnedMultiMesh","GameManager","CursorManager","Component","GameObject","Physics",
        "GamePhysics","TriggerLadder","WaterSystem","WaterBody","TerrainMeta","TerrainCollision",
        "Climate","ConVar_Player_Static","ConVar_Graphics_Static","ConVar_Client_Static",
        "ConVar_Admin_Static","ConVar_Culling_Static","BaseViewModel","Buildable","BuildingBlock",
        "BuildingPrivlidge","Door","Signage","ConsoleSystem","DroppedItem","DroppedItemContainer",
        "WorldItem","LootContainer","StorageContainer","PlayerLoot","ItemDefinition",
        "ListDictionary<NetworkableID>","ListComponent<Projectile>","TOD_Sky","TOD_CycleParameters",
        "TOD_DayParameters","TOD_NightParameters","HitTest","HitInfo","LocalPlayer",
        "MainCamera","Camera","Transform","Renderer","SkinnedMeshRenderer","Collider",
        "CapsuleCollider","Rigidbody","MonoBehaviour","Behaviour","Object"
    };
    if (exact.count(name))
        return "exact";

    // keyword scan - catches obfuscated-but-relevant classes and anything whose
    // name still describes a field we care about
    static const char* kws[] = {
        "health","Health","Inventory","inventory","EntityRealm","ClientEntities",
        "Networkable","PlayerModel","PlayerEyes","WalkMovement","BaseCombat",
        "Decrypt","decrypt","Projectile","ItemContainer","DroppedItem","Loot",
        "Camera","Sky","Graphics","Admin","Body","Capsule","ModelState","HitTest"
    };
    for (auto k : kws)
        if (name.find(k) != std::string::npos)
            return k;
    return nullptr;
}

inline bool IsTargetClass(const std::string& ns, const std::string& name)
{
    (void)ns;
    return TargetMatchReason(name) != nullptr;
}

inline bool IsKeyClass(const std::string& name)
{
    static const std::set<std::string> keys = {
        "BaseNetworkable", "BasePlayer", "BaseCombatEntity", "BaseEntity",
        "PlayerEyes", "PlayerModel", "PlayerWalkMovement", "PlayerInventory",
        "PlayerInput", "Item", "ItemContainer", "ItemDefinition", "HeldEntity",
        "BaseProjectile", "AttackEntity", "BaseMelee", "DroppedItem",
        "DroppedItemContainer", "BaseViewModel", "WorldItem", "Camera",
        "TOD_Sky", "GameManager", "ConsoleSystem", "BuildingBlock",
        "BuildingPrivlidge", "Door", "Signage"
    };
    return keys.count(name) != 0;
}

// Classes the regular-offset header actually exports.  Walking only these is
// what keeps a full dump at seconds instead of tens of minutes: every field
// accessor on this build is a protected trampoline, and the broad keyword
// match (Camera/Loot/Health/...) otherwise hits hundreds of classes.
inline bool IsDumpClass(const std::string& name)
{
    static const std::set<std::string> dump = {
        // entity tree / base
        "BaseNetworkable", "BaseEntity", "BaseCombatEntity", "BasePlayer",
        "BaseMountable", "BaseNpc", "BaseVehicle", "LocalPlayer", "GameManager",
        "ListComponent<Projectile>",
        // world items / containers
        "DroppedItem", "DroppedItemContainer", "WorldItem", "Item",
        "ItemContainer", "ItemDefinition", "ItemIcon", "ItemModProjectile",
        "ProjectileWeaponMod", "RecoilProperties", "HeldEntity", "ViewModel",
        "BaseViewModel", "StorageContainer", "LootContainer", "PlayerCorpse",
        "LootableCorpse", "HackableLockedCrate", "OreResourceEntity",
        "ResourceEntity", "CollectibleEntity", "GrowableEntity",
        // building / deployables
        "BuildingBlock", "BuildingPrivlidge", "Door", "Signage", "AutoTurret",
        "FlameTurret", "GunTrap", "TimedExplosive", "BaseLauncher",
        "BradleyAPC", "PatrolHelicopter",
        // player / combat
        "PlayerEyes", "PlayerModel", "PlayerInventory", "PlayerInput",
        "PlayerWalkMovement", "SkinnedMultiMesh", "Facepunch.Skeleton",
        "Skeleton", "Bone", "Model", "AttackEntity", "BaseMelee",
        "BaseProjectile", "CompoundBowWeapon", "FlintStrikeWeapon",
        "Projectile", "HitTest",
        // camera / sky / statics
        "Camera", "MainCamera", "TOD_Sky", "TOD_CycleParameters",
        "TOD_DayParameters", "TOD_NightParameters", "ConVar.Graphics",
        "ConVar.Admin", "ConsoleSystem", "PhysX", "MapInterface"
    };
    return dump.count(name) != 0 || IsKeyClass(name);
}

// Method tables are not needed for an offset header.  Every method name goes
// through a protected accessor (~100 ms on 26140533), so a class with 300
// methods used to cost half a minute.  Flip this to true if method RVAs are
// explicitly wanted for a reversing session.
constexpr bool kDumpMethods = false;

// Class initializers are not required for an offset/typeinfo dump.  Flip this
// on only when you need static field *values* of classes that are still cold.
constexpr bool kInitTargetStatics = false;

inline void* ResolveParent(void* klass)
{
    if (!klass) return nullptr;
    if (il2::class_get_parent)
    {
        void* p = il2::SafeClassGetParent((il2::Il2CppClass*)klass);
        if (p && p != klass)
            return p;
    }

    // this build hides the accessor in some revisions; metadata places parent at
    // klass+0x58 (confirmed live on LocalPlayer in 26140533)
    u64 p = ReadPtr((u64)klass + 0x58);
    if (p == (u64)klass || !LooksLikeKlass(p))
        return nullptr;
    return (void*)p;
}

// ---------------------------------------------------------------------------
//  enumerate every class of every assembly
// ---------------------------------------------------------------------------
inline bool EnumerateClasses(DumpResult& r)
{
    if (!il2::domain_get || !il2::domain_get_assemblies ||
        !il2::assembly_get_image || !il2::image_get_class_count ||
        !il2::image_get_class)
    {
        Log("[!] required IL2CPP enumeration exports are missing");
        Log("[!]   il2cpp_domain_get=%p domain_get_assemblies=%p assembly_get_image=%p",
            (void*)il2::domain_get, (void*)il2::domain_get_assemblies,
            (void*)il2::assembly_get_image);
        Log("[!]   image_get_class_count=%p image_get_class=%p class_get_fields=%p",
            (void*)il2::image_get_class_count, (void*)il2::image_get_class,
            (void*)il2::class_get_fields);
        return false;
    }

    const DWORD tStart = GetTickCount();

    bool domainOk = false;
    void* domain = il2::SafeDomainGet(&domainOk);
    if (!domain)
    {
        Log("[!] il2cpp_domain_get returned null - runtime not ready%s",
            domainOk ? "" : " (accessor faulted)");
        return false;
    }
    Log("[ENUM] il2cpp_domain_get -> 0x%llX", (unsigned long long)domain);

    if (il2::thread_attach)
    {
        bool taOk = false;
        void* ta = il2::SafeThreadAttach(domain, &taOk);
        Log("[ENUM] il2cpp_thread_attach -> 0x%llX%s", (unsigned long long)ta,
            ta ? "" : (taOk ? "  [returned null]" : "  [faulted - enumeration continues]"));
    }
    else
        Log("[ENUM] il2cpp_thread_attach export missing - running on the injected thread");

    size_t asmCount = 0;
    bool asmOk = false;
    il2::Il2CppAssembly** asms = il2::SafeDomainGetAssemblies(domain, &asmCount, &asmOk);
    Log("[+] assemblies: %zu (array=0x%llX)%s", asmCount, (unsigned long long)asms,
        asmOk ? "" : "  [accessor faulted]");
    if (!asms || !asmCount)
        return false;

    struct AsmStat
    {
        std::string name;
        size_t declared = 0;
        size_t walked = 0;
        size_t targets = 0;
        size_t unnamed = 0;
        size_t dup = 0;
        size_t unreadable = 0;
        DWORD  ms = 0;
    };
    std::vector<AsmStat> stats;
    stats.reserve(asmCount);

    std::unordered_set<u64> seen;
    size_t totalKlass = 0, totalFields = 0, totalMethods = 0, targetTotal = 0;
    size_t skippedUnreadable = 0, skippedDup = 0, skippedUnnamed = 0, skippedNonTarget = 0;
    size_t fieldWalkFaults = 0, methodWalkFaults = 0;
    size_t fieldsUnnamed = 0, fieldsNoType = 0, methodsUnnamed = 0, methodsNoCode = 0;
    size_t fieldWalkTruncated = 0, methodWalkTruncated = 0;

    for (size_t a = 0; a < asmCount; ++a)
    {
        AsmStat st;
        const DWORD tAsm = GetTickCount();

        il2::Il2CppImage* img = il2::SafeAssemblyGetImage(asms[a]);
        if (!img)
        {
            st.name = "<null-image>";
            st.ms = GetTickCount() - tAsm;
            stats.push_back(st);
            Log("[ASM] [%zu/%zu] assembly=0x%llX assembly_get_image -> null, skipped",
                a + 1, asmCount, (unsigned long long)asms[a]);
            continue;
        }

        std::string imgName;
        if (il2::image_get_name)
        {
            const char* in = il2::SafeImageGetNameRaw(img);
            if (in && MemReadable((u64)in, 1))
                imgName = ReadCStr((u64)in, 200);
            else
                Log("[ASM] [%zu/%zu] image_get_name returned unreadable pointer 0x%llX",
                    a + 1, asmCount, (unsigned long long)in);
        }
        else
            Log("[ASM] [%zu/%zu] il2cpp_image_get_name export missing", a + 1, asmCount);
        if (imgName.empty())
            imgName = "<unnamed>";
        st.name = imgName;

        bool countOk = false;
        size_t count = il2::SafeImageGetClassCount(img, &countOk);
        st.declared = count;
        if (!countOk)
        {
            Log("[ASM] [%zu/%zu] image='%s' image=0x%llX image_get_class_count FAULTED - skipped",
                a + 1, asmCount, imgName.c_str(), (unsigned long long)img);
            st.ms = GetTickCount() - tAsm;
            stats.push_back(st);
            continue;
        }

        Log("[ASM] [%zu/%zu] image='%s' image=0x%llX classes=%zu",
            a + 1, asmCount, imgName.c_str(), (unsigned long long)img, count);
        if (count > 200000)
            Log("[ASM][!] image='%s' reports %zu classes - suspicious, walking anyway",
                imgName.c_str(), count);

        // Build the flat TypeInfo table once, then never pay the protected
        // image_get_class trampoline again (it costs ~30 ms per class here).
        if (!il2::TypeTable().valid && count >= 4)
        {
            DWORD tTt = GetTickCount();
            bool built = il2::BuildTypeTable(img, count);
            Log("[ENUM] direct class table: %s (%lu ms)", built ? "FOUND" : "not found - falling back to exports",
                GetTickCount() - tTt);
        }

        u32 typeStart = 0xFFFFFFFFu;
        bool fastWalk = false;
        if (il2::TypeTable().valid)
        {
            typeStart = il2::ImageTypeStart(img);
            fastWalk = typeStart != 0xFFFFFFFFu;
        }

        for (size_t i = 0; i < count; ++i)
        {
            il2::Il2CppClass* k = fastWalk ? il2::FastImageGetClass(img, i, typeStart)
                                           : il2::SafeImageGetClass(img, i);
            if (!k || !MemReadable((u64)k, 0x100))
            {
                st.unreadable++;
                skippedUnreadable++;
                if (st.unreadable <= 3)
                    Log("[ASM][!] image='%s' class[%zu] -> 0x%llX unreadable/null, skipped",
                        imgName.c_str(), i, (unsigned long long)k);
                continue;
            }

            u64 ku = (u64)k;
            if (!seen.insert(ku).second)
            {
                st.dup++;
                skippedDup++;
                continue;
            }

            std::string nm = il2::KlassName(k);
            if (nm.empty())
            {
                st.unnamed++;
                skippedUnnamed++;
                if (st.unnamed <= 3)
                    Log("[ASM][!] image='%s' class[%zu] klass=0x%llX has no readable name, skipped",
                        imgName.c_str(), i, (unsigned long long)ku);
                continue;
            }

            ClassRow c;
            c.klass = k;
            c.name = DeobfuscateKlassName(nm);

            // Name-only target test first.  class_get_namespace /
            // class_get_parent / class_get_static_field_data are the expensive
            // calls on this protected build - never call them for the 10k+
            // classes we are not going to dump anyway.
            const char* reason = TargetMatchReason(c.name.c_str());
            c.target = reason != nullptr;

            if (!c.target)
                skippedNonTarget++;

            if (c.target)
            {
                c.ns = il2::KlassNamespace(k);
                c.parent = ResolveParent(k);
                bool staticOk = false;
                c.staticData = il2::SafeStaticFieldData(k, &staticOk);
                if (!staticOk && il2::class_get_static_field_data)
                    Log("[CLASS][!] %s class_get_static_field_data FAULTED", c.name.c_str());
                // Running a class initializer per target spawns arbitrary managed
                // code on the dump thread and dominates enumeration time.  Static
                // blocks are already resolvable without it; probes that need a
                // warm type call SafeRuntimeClassInit() themselves.
                if (kInitTargetStatics && il2::runtime_class_init)
                    il2::SafeRuntimeClassInit(k);

                std::string pn = c.parent ? il2::KlassName(c.parent) : "";
                Log("[CLASS] %s%s  klass=0x%llX parent=0x%llX('%s') static=0x%llX match='%s'",
                    c.ns.empty() ? "" : (c.ns + "::").c_str(), c.name.c_str(),
                    (unsigned long long)ku,
                    (unsigned long long)c.parent, pn.c_str(),
                    (unsigned long long)c.staticData, reason ? reason : "?");
                if (!c.parent)
                    Log("[CLASS][!] %s has no parent (class_get_parent missing or faulted)",
                        c.name.c_str());
                if (!c.staticData)
                    Log("[CLASS][!] %s static block is 0 (no static fields, or export failed)",
                        c.name.c_str());
            }

            // fields - only for classes we actually export.  Walking every
            // field of 10k+ classes through the protected accessors takes
            // minutes; the regular-offset header only needs this curated set.
            if (c.target && IsDumpClass(c.name))
            {
                void* iter = nullptr;
                int guard = 0;
                bool faulted = false;
                while (guard++ < 2048 && il2::class_get_fields)
                {
                    il2::Il2CppField* f = nullptr;
                    if (!il2::SafeClassGetFields(k, &iter, &f))
                    {
                        faulted = true;
                        fieldWalkFaults++;
                        Log("[CLASS][!] field walk FAULT in %s (klass=0x%llX) after %zu field(s) - layout incomplete",
                            c.name.c_str(), (unsigned long long)ku, c.fields.size());
                        break;
                    }
                    if (!f)
                        break;
                    if (!MemReadable((u64)f, 0x20))
                    {
                        Log("[CLASS][!] %s field[%zu] descriptor 0x%llX unreadable - walk stopped",
                            c.name.c_str(), c.fields.size(), (unsigned long long)f);
                        break;
                    }

                    FieldRow fr;
                    fr.field = f;
                    size_t off = 0;
                    if (!il2::SafeFieldOffset(f, &off))
                    {
                        Log("[CLASS][!] %s field descriptor=0x%llX field_get_offset FAULTED - slot skipped",
                            c.name.c_str(), (unsigned long long)f);
                        continue;
                    }
                    if (off > 0x100000)
                    {
                        Log("[CLASS][!] %s field descriptor=0x%llX reports offset 0x%llX - implausible, slot skipped",
                            c.name.c_str(), (unsigned long long)f, (unsigned long long)off);
                        continue;
                    }
                    fr.offset = (u32)off;
                    fr.rawName = il2::FieldName(f);
                    fr.typeName = il2::FieldTypeName(f);
                    fr.name = DeobfuscateFieldName(c.name, fr.rawName, fr.offset, fr.typeName);
                    if (fr.name.empty() || fr.name[0] == '%')
                    {
                        // Obfuscated name that the hash table cannot resolve (the
                        // token is a one-way hash).  Keep the slot usable: emit a
                        // stable offset-based identifier.  The raw hash is kept in
                        // rawName and recorded in Rust-Offset-Dumper_hash_names.txt.
                        char nb[32];
                        sprintf_s(nb, sizeof(nb), "field_0x%X", fr.offset);
                        fr.name = nb;
                        fieldsUnnamed++;
                    }
                    int fl = 0;
                    if (!il2::SafeFieldFlags(f, &fl))
                        Log("[CLASS][!] %s field '%s' field_get_flags FAULTED - flags assumed 0",
                            c.name.c_str(), fr.name.c_str());
                    fr.flags = (u32)fl;
                    {
                        char tctx[200];
                        sprintf_s(tctx, sizeof(tctx), "type of %s+0x%X", c.name.c_str(), fr.offset);
                        fr.typeName = ResolveHashTokens(fr.typeName, tctx);
                    }
                    if (fr.typeName.empty())
                        fieldsNoType++;
                    c.fields.push_back(std::move(fr));
                    totalFields++;
                }
                if (!faulted && guard >= 2048)
                {
                    fieldWalkTruncated++;
                    Log("[CLASS][!] %s field walk hit the 2048-field guard - truncated",
                        c.name.c_str());
                }
                if (c.fields.empty())
                    Log("[CLASS][!] %s resolved 0 fields (class_get_fields%s)",
                        c.name.c_str(), il2::class_get_fields ? " walked" : " export missing");
            }

            // methods only for interesting classes - otherwise the dump is 10x
            // larger and the useful RVAs drown.  On this build every method
            // name is a protected call, so methods are off by default (see
            // kDumpMethods) - an offset header does not need them.
            if (kDumpMethods && c.target && IsDumpClass(c.name) && il2::class_get_methods)
            {
                void* mi = nullptr;
                int mg = 0;
                while (mg++ < 4096)
                {
                    il2::Il2CppMethod* m = nullptr;
                    if (!il2::SafeClassGetMethods(k, &mi, &m))
                    {
                        methodWalkFaults++;
                        Log("[CLASS][!] method walk FAULT in %s (klass=0x%llX) after %zu method(s)",
                            c.name.c_str(), (unsigned long long)ku, c.methods.size());
                        break;
                    }
                    if (!m || !MemReadable((u64)m, 0x20))
                        break;

                    char mn[200]{};
                    if (!il2::SafeMethodName(m, mn, sizeof(mn)))
                    {
                        methodsUnnamed++;
                        continue;
                    }
                    MethodRow mr;
                    mr.method = m;
                    mr.name = mn;
                    int argc = 0;
                    if (!il2::SafeMethodParamCount(m, &argc))
                        Log("[CLASS][!] %s::%s method_get_param_count FAULTED - argc=0",
                            c.name.c_str(), mr.name.c_str());
                    mr.argc = argc;
                    // MethodInfo::methodPointer is the first qword on this build
                    mr.code = ReadPtr((u64)m);
                    u64 imgSize = r.imageSize;
                    if (mr.code >= r.gameAssembly && (!imgSize || mr.code < r.gameAssembly + imgSize))
                        mr.rva = mr.code - r.gameAssembly;
                    else
                    {
                        mr.rva = 0;
                        if (mr.code)
                            methodsNoCode++;
                    }
                    c.methods.push_back(std::move(mr));
                    totalMethods++;
                }
                if (mg >= 4096)
                {
                    methodWalkTruncated++;
                    Log("[CLASS][!] %s method walk hit the 4096-method guard - truncated",
                        c.name.c_str());
                }
            }
            else if (kDumpMethods && c.target && IsDumpClass(c.name))
                Log("[CLASS][!] %s has no method list (il2cpp_class_get_methods export missing)",
                    c.name.c_str());

            if (c.target && IsKeyClass(c.name))
            {
                Log("[LAYOUT] %s%s fields=%zu methods=%zu",
                    c.ns.empty() ? "" : (c.ns + "::").c_str(), c.name.c_str(),
                    c.fields.size(), c.methods.size());
                for (auto& fr : c.fields)
                {
                    Log("    +0x%04X %-8s %-40s %s",
                        fr.offset,
                        (fr.flags & 0x10) ? "static" : "instance",
                        fr.name.c_str(),
                        fr.typeName.empty() ? "<no type name>" : fr.typeName.c_str());
                }
            }

            if (c.target)
                st.targets++;

            r.klassSet.insert(ku);
            r.classes.push_back(std::move(c));
            totalKlass++;
            if (r.classes.back().target)
                targetTotal++;
            if ((totalKlass % 2000) == 0)
            {
                DWORD el = GetTickCount() - tStart;
                Log("[.] enumerated %zu classes, %zu fields, %zu methods, %zu targets... (%lu ms, %.0f classes/s)",
                    totalKlass, totalFields, totalMethods, targetTotal,
                    el, el ? (totalKlass * 1000.0 / el) : 0.0);
            }
        }

        st.walked = totalKlass;
        st.ms = GetTickCount() - tAsm;
        stats.push_back(st);

        Log("[ASM] done '%s': declared=%zu kept=%zu targets=%zu unnamed=%zu dup=%zu unreadable=%zu  %lu ms",
            imgName.c_str(), count, st.walked, st.targets, st.unnamed, st.dup,
            st.unreadable, st.ms);
    }

    Log("[+] classes: %zu, fields: %zu, methods: %zu, target classes: %zu (enumerated in %lu ms)",
        totalKlass, totalFields, totalMethods, targetTotal, GetTickCount() - tStart);
    Log("[ENUM] skipped: unreadable=%zu duplicate=%zu unnamed=%zu non-target=%zu",
        skippedUnreadable, skippedDup, skippedUnnamed, skippedNonTarget);
    Log("[ENUM] walk faults: fields=%zu methods=%zu | unnamed fields=%zu, fields without type=%zu, "
        "unnamed methods=%zu, methods with out-of-module code=%zu | guards hit: fields=%zu methods=%zu",
        fieldWalkFaults, methodWalkFaults, fieldsUnnamed, fieldsNoType,
        methodsUnnamed, methodsNoCode, fieldWalkTruncated, methodWalkTruncated);
    Log("[ENUM] per-assembly summary:");
    for (auto& s : stats)
        Log("[ENUM]   %-44s declared=%6zu total=%6zu targets=%4zu unnamed=%4zu dup=%4zu bad=%4zu %6lu ms",
            s.name.c_str(), s.declared, s.walked, s.targets, s.unnamed, s.dup,
            s.unreadable, s.ms);

    return totalKlass != 0;
}

// ---------------------------------------------------------------------------
//  typeinfo RVA finder: every qword in the image that equals a live klass ptr
// ---------------------------------------------------------------------------
inline void ScanTypeInfos(DumpResult& r)
{
    if (!r.gameAssembly || !r.imageSize)
    {
        Log("[SCAN][!] skipped: gameAssembly=0x%llX imageSize=0x%llX",
            (unsigned long long)r.gameAssembly, (unsigned long long)r.imageSize);
        return;
    }

    const DWORD tStart = GetTickCount();
    auto sections = GetPeSections(r.gameAssembly);
    Log("[SCAN] PE sections of GameAssembly=0x%llX (SizeOfImage=0x%llX, klass set=%zu):",
        (unsigned long long)r.gameAssembly, (unsigned long long)r.imageSize,
        r.klassSet.size());
    for (auto& s : sections)
        Log("    %-8s va=0x%08llX vsize=0x%08llX chars=0x%08X %s",
            s.name.c_str(), (unsigned long long)s.va,
            (unsigned long long)s.vsize, s.chars,
            (s.chars & IMAGE_SCN_MEM_EXECUTE) ? "(code, skipped)" : "");

    if (sections.empty())
    {
        Log("[SCAN][!] no PE sections readable - typeinfo scan impossible");
        return;
    }

    u64 scanned = 0, hits = 0, overflow = 0;
    u64 lastReport = 0;
    size_t execSections = 0, dataSections = 0, truncatedSections = 0;

    for (auto& s : sections)
    {
        // skip executable code - klass pointers there would be immediates in
        // instructions, too noisy to be useful
        if (s.chars & IMAGE_SCN_MEM_EXECUTE)
        {
            execSections++;
            continue;
        }
        dataSections++;

        u64 start = r.gameAssembly + s.va;
        u64 end   = start + s.vsize;
        if (end <= start)
        {
            Log("[SCAN] section '%s' has empty virtual range (vsize=0x%llX) - skipped",
                s.name.c_str(), (unsigned long long)s.vsize);
            continue;
        }

        u64 cur = start;
        u64 sectionHitsBefore = hits;
        u64 sectionClassesBefore = r.typeInfoRvas.size();
        DWORD tSec = GetTickCount();

        Log("[SCAN] section '%s' start=0x%llX end=0x%llX size=0x%llX",
            s.name.c_str(), (unsigned long long)start,
            (unsigned long long)end, (unsigned long long)(end - start));

        while (cur + 8 <= end)
        {
            MEMORY_BASIC_INFORMATION mbi{};
            if (VirtualQuery((LPCVOID)cur, &mbi, sizeof(mbi)) != sizeof(mbi))
            {
                Log("[SCAN][!] VirtualQuery failed at 0x%llX (err=%lu), stop section",
                    (unsigned long long)cur, GetLastError());
                break;
            }
            if (mbi.State != MEM_COMMIT || (mbi.Protect & (PAGE_NOACCESS | PAGE_GUARD)))
            {
                u64 next = (u64)mbi.BaseAddress + mbi.RegionSize;
                if (next <= cur)
                    next = cur + 0x1000;
                Log("[SCAN] skip non-committed region 0x%llX..0x%llX state=0x%lX protect=0x%lX",
                    (unsigned long long)cur, (unsigned long long)next,
                    mbi.State, mbi.Protect);
                cur = next;
                continue;
            }

            u64 regionEnd = (u64)mbi.BaseAddress + mbi.RegionSize;
            u64 scanEnd = (std::min)(end, regionEnd);
            u64 blockStart = cur;

            for (; cur + 8 <= scanEnd; cur += 8)
            {
                u64 v = 0;
                memcpy(&v, (const void*)cur, 8);
                if (!v) continue;

                u32 rva = (u32)(cur - r.gameAssembly);
                if (r.klassSet.find(v) != r.klassSet.end())
                {
                    auto& vec = r.typeInfoRvas[v];
                    if (vec.size() < 16)
                        vec.push_back(rva);
                    else
                        overflow++;
                    hits++;
                    continue;
                }

                // not-yet-initialised TypeInfo slot: record the usage token
                if (v <= 0xFFFFFFFFull &&
                    ExpectedTypeInfoTokens().count((u32)v))
                {
                    auto& vec = r.typeInfoTokenRvas[(u32)v];
                    if (vec.size() < 16)
                        vec.push_back(rva);
                    else
                        overflow++;
                    hits++;
                }
            }
            scanned += (cur - blockStart);

            if ((scanned - lastReport) >= (64ull << 20))
            {
                lastReport = scanned;
                u64 total = r.imageSize ? r.imageSize : 1;
                Log("[SCAN] ... scanned 0x%llX / 0x%llX (%llu%%)  hits=%llu  mapped=%zu  %lu ms",
                    (unsigned long long)scanned, (unsigned long long)r.imageSize,
                    (unsigned long long)((scanned * 100) / total),
                    (unsigned long long)hits, r.typeInfoRvas.size(),
                    GetTickCount() - tStart);
            }
        }

        if (cur < end)
            truncatedSections++;

        Log("[SCAN] section '%s' done: scanned=0x%llX hits=%llu new-klass=%zu %lu ms",
            s.name.c_str(), (unsigned long long)(cur - start),
            (unsigned long long)(hits - sectionHitsBefore),
            r.typeInfoRvas.size() - sectionClassesBefore,
            GetTickCount() - tSec);
    }

    Log("[SCAN] walk done: %zu data section(s), %zu code section(s) skipped, %zu section(s) "
        "partially mapped, scanned=0x%llX of 0x%llX, %llu hit(s), %zu klass mapping(s), "
        "%llu overflow slot(s), %lu ms",
        dataSections, execSections, truncatedSections,
        (unsigned long long)scanned, (unsigned long long)r.imageSize,
        (unsigned long long)hits, r.typeInfoRvas.size(),
        (unsigned long long)overflow, GetTickCount() - tStart);

    size_t multiSlot = 0;
    for (auto& kv : r.typeInfoRvas)
        if (kv.second.size() > 1)
            multiSlot++;
    Log("[SCAN] candidate distribution: %zu klass with 1 slot, %zu klass with 2+ slot(s)",
        r.typeInfoRvas.size() - multiSlot, multiSlot);

    u64 targetCount = 0, targetWithTypeinfo = 0;
    for (auto& c : r.classes)
    {
        if (!c.target)
            continue;
        targetCount++;
        auto it = r.typeInfoRvas.find((u64)c.klass);
        if (it == r.typeInfoRvas.end())
        {
            Log("[TYPEINFO][MISS] %s%s klass=0x%llX - no slot found in any data section",
                c.ns.empty() ? "" : (c.ns + "::").c_str(), c.name.c_str(),
                (unsigned long long)c.klass);
            continue;
        }
        targetWithTypeinfo++;
        char line[512]{};
        int pos = sprintf_s(line, sizeof(line), "[TYPEINFO] %s%s klass=0x%llX ->",
            c.ns.empty() ? "" : (c.ns + "::").c_str(), c.name.c_str(),
            (unsigned long long)c.klass);
        for (u32 rva : it->second)
        {
            if (pos < (int)sizeof(line) - 24)
                pos += sprintf_s(line + pos, sizeof(line) - pos, " 0x%X", rva);
        }
        Log("%s", line);
    }

    Log("[+] typeinfo scan done: %llu pointer hit(s), %zu klass mapping(s), targets %llu/%llu",
        (unsigned long long)hits, r.typeInfoRvas.size(),
        (unsigned long long)targetWithTypeinfo, (unsigned long long)targetCount);
}

// ---------------------------------------------------------------------------
//  clean offsets: only real (non-obfuscated) names + their typeinfo RVAs
// ---------------------------------------------------------------------------
inline bool IsHashedIdent(const std::string& s)
{
    // EAC renders hidden names as "%<40 hex>" before sanitising; the sanitised
    // form is "_<40 hex>".  Anything else is treated as a real identifier.
    size_t start = 0;
    if (!s.empty() && s[0] == '%') start = 1;
    else if (!s.empty() && s[0] == '_') start = 1;
    else return false;
    if (s.size() != start + 40) return false;
    for (size_t i = start; i < s.size(); ++i)
    {
        char c = s[i];
        if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f') || (c >= 'A' && c <= 'F')))
            return false;
    }
    return true;
}

// A hashed token can hide inside a generic/qualified name (ListComponent<%hash>,
// SomeNs::%hash). Match a run of 32+ hex characters anywhere in the string.
inline bool ContainsHashToken(const std::string& s)
{
    size_t i = 0;
    while (i < s.size())
    {
        char c = s[i];
        const bool hex = (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f') || (c >= 'A' && c <= 'F');
        if (!hex) { ++i; continue; }
        size_t j = i;
        while (j < s.size())
        {
            char d = s[j];
            if (!((d >= '0' && d <= '9') || (d >= 'a' && d <= 'f') || (d >= 'A' && d <= 'F')))
                break;
            ++j;
        }
        if (j - i >= 32) return true;
        i = j;
    }
    return false;
}

inline bool IsCompilerGeneratedName(const std::string& s)
{
    return s.empty() || s[0] == '<' || s[0] == '$' ||
        s.find("DisplayClass") != std::string::npos ||
        s.compare(0, 3, "__c") == 0 ||
        s.compare(0, 7, "field_0x") == 0;
}

// ---------------------------------------------------------------------------
//  static offset tables (live port of revers/rev_binary.py)
//
//  For every dumped class we try to pin its `fieldOffsets` int32 array in the
//  mapped .rdata image.  The anchors are the fields whose metadata name is
//  readable - their live offset is what the runtime really uses, so the table
//  must agree with it entry by entry.  Hidden (%hash) fields never anchor the
//  search; they are the slots the table is used to recover when the live
//  accessor could not produce a plausible offset.
// ---------------------------------------------------------------------------
inline void ApplyStaticTables(DumpResult& r)
{
    if (!r.gameAssembly)
        return;

    size_t clsFound = 0, clsNoTable = 0, filledTotal = 0, verifiedTotal = 0;

    for (auto& c : r.classes)
    {
        if (!c.target || !IsDumpClass(c.name) || c.fields.empty())
            continue;

        std::vector<staticscan::Anchor> anchors;
        anchors.reserve(c.fields.size());
        for (u32 i = 0; i < (u32)c.fields.size(); ++i)
        {
            const FieldRow& fr = c.fields[i];
            if (fr.flags & 0x10)                              // static
                continue;
            if (!staticscan::PlausibleOffset(fr.offset))
                continue;
            if (staticscan::HashLikeName(fr.rawName))         // hidden: not an anchor
                continue;
            anchors.push_back({ i, fr.offset });
        }

        c.tableAnchors = (int)anchors.size();
        const staticscan::TableHit hit =
            staticscan::FindFieldOffsetTable(r.gameAssembly, (u32)c.fields.size(), anchors);

        if (!hit.found)
        {
            ++clsNoTable;
            for (FieldRow& fr : c.fields)
                if (!(fr.flags & 0x10))
                    fr.evidence = 1;                          // live only
            Log("[STATIC] %s: no verified .rdata offset table (anchors=%d) - "
                "offset stands on the live runtime",
                c.name.c_str(), c.tableAnchors);
            continue;
        }

        ++clsFound;
        c.tableFound = true;
        c.tableRva = hit.rva;

        for (u32 i = 0; i < (u32)c.fields.size(); ++i)
        {
            FieldRow& fr = c.fields[i];
            if (fr.flags & 0x10)
            {
                fr.evidence = 1;                              // statics are not in the table
                continue;
            }
            const int v = (i < hit.values.size()) ? hit.values[i] : staticscan::kPoison;

            if (!staticscan::HashLikeName(fr.rawName) && staticscan::PlausibleOffset(fr.offset))
            {
                fr.evidence = 2;                              // anchor: table == live
                ++c.tableVerified;
                ++verifiedTotal;
                continue;
            }

            // hidden slot: the live offset is missing/implausible - take the
            // table value, but only a real one (poison stays a hole).
            if (v != staticscan::kPoison && v > 0 && v <= 0x100000 &&
                !staticscan::PlausibleOffset(fr.offset))
            {
                fr.offset = (u32)v;
                fr.evidence = 3;
                ++c.tableFilled;
                ++filledTotal;
                if (fr.name.empty() || staticscan::HashLikeName(fr.name))
                {
                    const char* nn = revers_offsets::NameFor(c.name.c_str(), fr.offset);
                    if (nn)
                        fr.name = nn;
                }
            }
            else
            {
                fr.evidence = staticscan::PlausibleOffset(fr.offset) ? 2 : 1;
                if (fr.evidence == 2)
                    ++verifiedTotal;
            }
        }

        Log("[STATIC] %s: table 0x%X pinned by %d anchor(s), %d slot(s) verified, %d recovered",
            c.name.c_str(), c.tableRva, c.tableAnchors, c.tableVerified, c.tableFilled);
    }

    Log("[STATIC] summary: %zu class table(s) pinned, %zu without a table, "
        "%zu live offset(s) verified, %zu slot(s) recovered from .rdata",
        clsFound, clsNoTable, verifiedTotal, filledTotal);
}

inline void WriteCleanOffsets(const DumpResult& r, const std::string& path)
{
    std::ofstream f(path, std::ios::binary);
    if (!f)
    {
        Log("[WRITE][!] cannot open %s", path.c_str());
        return;
    }

    Log("[WRITE] generating clean offsets (no hashed names): %s", path.c_str());
    f << "// ============================================================================\n";
    f << "//  Rust-Offset-Dumper CLEAN offsets - only named classes/fields, no EAC hashes\n";
    f << "//  generated: " << r.timestamp << "\n";
    f << "//  GameAssembly base: 0x" << std::hex << r.gameAssembly << std::dec << "\n";
    f << "//  Every typeinfo_rva here is a real GameAssembly data slot from\n";
    f << "//  Rust-Offset-Dumper_typeinfos.txt for a class whose name is not obfuscated.\n";
    f << "// ============================================================================\n\n";
    f << "#pragma once\n#include <cstddef>\n#include <cstdint>\n\n";
    f << "namespace clean\n{\n";

    std::vector<const ClassRow*> sorted;
    for (auto& c : r.classes)
        if (!IsHashedIdent(c.name) && !ContainsHashToken(c.name))
            sorted.push_back(&c);
    std::sort(sorted.begin(), sorted.end(), [](const ClassRow* a, const ClassRow* b) {
        if (a->name != b->name) return a->name < b->name;
        return a->ns < b->ns;
        });

    size_t classCount = 0, fieldCount = 0, rvaCount = 0;
    std::set<std::string> usedNs;
    for (auto* c : sorted)
    {
        std::vector<const FieldRow*> named;
        for (auto& fr : c->fields)
        {
            if (IsHashedIdent(fr.name) || ContainsHashToken(fr.name)) continue;
            if (IsCompilerGeneratedName(fr.name)) continue;  // unnamed/compiler slot
            named.push_back(&fr);
        }

        auto it = r.typeInfoRvas.find((u64)c->klass);
        bool hasRva = it != r.typeInfoRvas.end() && !it->second.empty();
        if (named.empty() && (!c->target || !hasRva))
            continue;
        if (IsCompilerGeneratedName(c->name))
            continue;

        std::string base = SanitizeIdent(c->name);
        std::string uniq = base;
        int n = 1;
        while (usedNs.count(uniq))
            uniq = base + "_" + std::to_string(++n);
        usedNs.insert(uniq);
        ++classCount;

        f << "    // " << Qualified(*c) << "  klass=0x" << std::hex << (u64)c->klass
          << std::dec << "\n";
        f << "    namespace " << uniq << "\n    {\n";

        if (hasRva)
        {
            u32 first = it->second.front();
            f << "        static constexpr std::uint32_t typeinfo_rva = 0x"
              << std::hex << first << std::dec << ";\n";
            ++rvaCount;
            if (it->second.size() > 1)
            {
                f << "        // other candidates:";
                for (size_t i = 1; i < it->second.size(); ++i)
                    f << " 0x" << std::hex << it->second[i] << std::dec;
                f << "\n";
            }
        }

        std::set<std::string> usedFields;
        for (auto* fr : named)
        {
            std::string fn = SanitizeIdent(fr->name);
            std::string baseFn = fn;
            int k = 1;
            while (usedFields.count(fn))
                fn = baseFn + "_" + std::to_string(++k);
            usedFields.insert(fn);

            f << "        static constexpr std::size_t " << fn << " = 0x"
              << std::hex << fr->offset << std::dec << ";";
            f << ((fr->flags & 0x10) ? " // static" : " // instance");
            f << "\n";
            ++fieldCount;
        }
        f << "    }\n\n";
    }
    f << "} // namespace clean\n";
    f.flush();
    f.close();
    LogFileWritten(path);
    Log("[WRITE] clean offsets: %zu class(es), %zu named field(s), %zu typeinfo rva(s)",
        classCount, fieldCount, rvaCount);
}

inline void WriteDecryptsHeader(const DumpResult& r, const std::string& path)
{
    std::ofstream f(path, std::ios::binary);
    if (!f)
    {
        Log("[WRITE][!] cannot open %s", path.c_str());
        return;
    }
    Log("[WRITE] generating decryptor header: %s", path.c_str());

    f << "// ============================================================================\n";
    f << "//  Rust-Offset-Dumper decryptors - " << r.timestamp << "\n";
    f << "//  GameAssembly base at dump time: 0x" << std::hex << r.gameAssembly << std::dec << "\n";
    f << "//\n";
    f << "//  These algorithms were recovered from GameAssembly.dll by tools/reverse.py\n";
    f << "//  and checked against the live binary (see Decryptors.generated.h).\n";
    f << "//  client_entities/entity_list take the HiddenValue wrapper pointer (a1); they\n";
    f << "//  read the populated flag at +0x10 and the encrypted qword at +0x18.\n";
    f << "//  clActiveItem takes the encrypted qword itself (no wrapper).\n";
    f << "//  FOV pair was supplied by the user; not auto-verified by reverse.py.\n";
    f << "//\n";
    f << "//  RD_READ(T, addr) can be overridden for a driver/remote reader.\n";
    f << "//  RD_GCHANDLE(x) can be overridden with il2cpp_gchandle_get_target.\n";
    f << "// ============================================================================\n";
    f << "#pragma once\n#include <cstdint>\n\n";
    f << "#ifndef RD_READ\n#define RD_READ(T, addr) (*reinterpret_cast<volatile T*>(addr))\n#endif\n";
    f << "#ifndef RD_GCHANDLE\n#define RD_GCHANDLE(x) (x)\n#endif\n\n";
    f << "namespace decryption\n{\n";
    f << R"CPP(
    inline constexpr std::uint64_t kClientEntitiesRva = 0x55A5C9D;
    inline constexpr std::uint64_t kEntityListRva      = 0x1C5C550;
    inline constexpr std::uint64_t kPlayerEyesRva      = 0x4030CF0;
    inline constexpr std::uint64_t kPlayerInventoryRva = 0x3E204A8;
    inline constexpr std::uint64_t kClActiveItemRva    = 0x3E8E5E0;

    inline std::uint32_t client_entities_word(std::uint32_t v)
    {
        v = v - 0x49F666DDu;
        v = v ^ 0x0165993Au;
        v = (v << 12) | (v >> 20);
        v = v ^ 0x06EA51C6u;
        return v;
    }

    inline std::uint64_t client_entities(std::uint64_t a1)
    {
        if (!RD_READ(std::uint8_t, a1 + 0x10)) return 0;
        std::uint64_t raw = RD_READ(std::uint64_t, a1 + 0x18);
        std::uint32_t lo = client_entities_word((std::uint32_t)raw);
        std::uint32_t hi = client_entities_word((std::uint32_t)(raw >> 32));
        return RD_GCHANDLE(((std::uint64_t)hi << 32) | lo);
    }

    inline std::uint32_t entity_list_word(std::uint32_t v)
    {
        v = v + 0x606A395Cu;
        v = (v << 17) | (v >> 15);
        v = v - 0x380CDD1Cu;
        return v;
    }

    inline std::uint64_t entity_list(std::uint64_t a1)
    {
        if (!RD_READ(std::uint8_t, a1 + 0x10)) return 0;
        std::uint64_t raw = RD_READ(std::uint64_t, a1 + 0x18);
        std::uint32_t lo = entity_list_word((std::uint32_t)raw);
        std::uint32_t hi = entity_list_word((std::uint32_t)(raw >> 32));
        return RD_GCHANDLE(((std::uint64_t)hi << 32) | lo);
    }

    inline std::uint32_t clActiveItem_word(std::uint32_t v)
    {
        v = (v << 2) | (v >> 30);
        v = v ^ 0xEC201AFBu;
        v = v + 0x3D62F8BAu;
        v = (v << 16) | (v >> 16);
        return v;
    }

    inline std::uint64_t clActiveItem(std::uint64_t raw)
    {
        std::uint32_t lo = clActiveItem_word((std::uint32_t)raw);
        std::uint32_t hi = clActiveItem_word((std::uint32_t)(raw >> 32));
        return ((std::uint64_t)hi << 32) | lo;
    }

    // Address-based convenience wrapper for the same cipher.
    inline std::uint64_t clActiveItem_ptr(std::uint64_t addr)
    {
        return clActiveItem(RD_READ(std::uint64_t, addr));
    }

    inline std::uint32_t PlayerInventory_word(std::uint32_t v)
    {
        v = (v << 2) | (v >> 30);
        v = v + 0xA0EB8D31u;
        v = (v << 31) | (v >> 1);
        v = v - 0x133B75FCu;
        return v;
    }

    inline std::uint64_t PlayerInventory(std::uint64_t a1)
    {
        if (!RD_READ(std::uint8_t, a1 + 0x10)) return 0;
        std::uint64_t raw = RD_READ(std::uint64_t, a1 + 0x18);
        std::uint32_t lo = PlayerInventory_word((std::uint32_t)raw);
        std::uint32_t hi = PlayerInventory_word((std::uint32_t)(raw >> 32));
        return RD_GCHANDLE(((std::uint64_t)hi << 32) | lo);
    }

    inline std::uint32_t PlayerEyes_word(std::uint32_t v)
    {
        v = v ^ 0x8D1FB868u;
        v = (v << 13) | (v >> 19);
        v = v ^ 0xBD80150Du;
        v = v + 0x5AA25993u;
        return v;
    }

    inline std::uint64_t PlayerEyes(std::uint64_t a1)
    {
        if (!RD_READ(std::uint8_t, a1 + 0x10)) return 0;
        std::uint64_t raw = RD_READ(std::uint64_t, a1 + 0x18);
        std::uint32_t lo = PlayerEyes_word((std::uint32_t)raw);
        std::uint32_t hi = PlayerEyes_word((std::uint32_t)(raw >> 32));
        return RD_GCHANDLE(((std::uint64_t)hi << 32) | lo);
    }

    // BasePlayer local-player wrapper uses the same cipher as client_entities.
    inline std::uint64_t local_player(std::uint64_t a1)
    {
        return client_entities(a1);
    }

    // ConVar.Graphics FOV (supplied pair; invertible).
    inline std::uint32_t decrypt_fov(std::uint32_t val)
    {
        val = (val << 4) | (val >> 28);
        val += 0x4E30062Eu;
        val = (val << 29) | (val >> 3);
        val ^= 0x74A660FAu;
        return val;
    }

    inline std::uint32_t encrypt_fov(std::uint32_t val)
    {
        val ^= 0x74A660FAu;
        val = (val >> 29) | (val << 3);
        val -= 0x4E30062Eu;
        val = (val >> 4) | (val << 28);
        return val;
    }
)CPP";
    f << "} // namespace decryption\n";
    f.flush();
    f.close();
    LogFileWritten(path);
}

// ---------------------------------------------------------------------------
//  output: single combined offset.h
//  [EXPORTS] block, then namespace offset (named fields only), then
//  namespace decrypt (RVAs), then the decryptor implementations.
// ---------------------------------------------------------------------------
inline std::string ReadWholeFile(const std::string& path)
{
    std::ifstream in(path, std::ios::binary);
    if (!in) return {};
    std::ostringstream ss;
    ss << in.rdbuf();
    return ss.str();
}

inline bool ExtractBetween(const std::string& src, const std::string& begin,
    const std::string& end, std::string& out)
{
    const size_t a = src.find(begin);
    if (a == std::string::npos) return false;
    const size_t body = a + begin.size();
    const size_t b = src.find(end, body);
    if (b == std::string::npos) return false;
    out = src.substr(body, b - body);
    return true;
}

inline void AppendExportScan(std::ostream& f)
{
    struct Entry { const char* name; bool required; };
    static const Entry entries[] = {
        { "il2cpp_domain_get", true },
        { "il2cpp_thread_attach", false },
        { "il2cpp_domain_get_assemblies", true },
        { "il2cpp_assembly_get_image", true },
        { "il2cpp_image_get_class_count", true },
        { "il2cpp_image_get_class", true },
        { "il2cpp_image_get_name", false },
        { "il2cpp_class_get_name", true },
        { "il2cpp_class_get_namespace", false },
        { "il2cpp_class_get_parent", false },
        { "il2cpp_class_get_fields", true },
        { "il2cpp_class_get_methods", false },
        { "il2cpp_class_get_static_field_data", false },
        { "il2cpp_class_get_type", false },
        { "il2cpp_class_from_name", false },
        { "il2cpp_field_get_name", false },
        { "il2cpp_field_get_offset", true },
        { "il2cpp_field_get_flags", false },
        { "il2cpp_field_get_type", false },
        { "il2cpp_field_static_get_value", false },
        { "il2cpp_method_get_name", false },
        { "il2cpp_method_get_param_count", false },
        { "il2cpp_method_get_param_name", false },
        { "il2cpp_method_get_param", false },
        { "il2cpp_type_get_name", false },
        { "il2cpp_type_get_object", false },
        { "il2cpp_runtime_class_init", false },
        { "il2cpp_gchandle_get_target", false },
        { "il2cpp_runtime_invoke", false },
        { "il2cpp_object_new", false },
    };
    const size_t n = sizeof(entries) / sizeof(entries[0]);

    u64 addrs[sizeof(entries) / sizeof(entries[0])]{};
    const char* fwd[sizeof(entries) / sizeof(entries[0])]{};
    for (size_t i = 0; i < n; ++i)
        addrs[i] = GetExportEx(il2::module, entries[i].name, &fwd[i]);

    int found = 0, missing = 0, aliased = 0, outOfRange = 0;
    f << "// [EXPORTS] GameAssembly export scan (module=0x" << std::hex
      << il2::module << std::dec << "):\n";
    for (size_t i = 0; i < n; ++i)
    {
        const Entry& e = entries[i];
        if (!addrs[i])
        {
            ++missing;
            if (fwd[i])
                f << "//   [FWD ] " << e.name << " -> forwarder '" << fwd[i] << "'\n";
            else
                f << "//   [MISS] " << e.name << "   ("
                  << (e.required ? "REQUIRED" : "optional") << ")\n";
            continue;
        }
        ++found;

        const char* aliasOf = nullptr;
        for (size_t j = 0; j < i; ++j)
            if (addrs[j] == addrs[i]) { aliasOf = entries[j].name; break; }
        if (aliasOf) ++aliased;

        bool inRange = false;
        if (il2::module)
        {
            const u64 size = GetPeSizeOfImage(il2::module);
            inRange = addrs[i] >= il2::module && (!size || addrs[i] < il2::module + size);
        }
        if (!inRange) ++outOfRange;

        f << "//   [ OK ] " << e.name << " = 0x" << std::hex << addrs[i]
          << "  (+0x" << (addrs[i] - il2::module) << ")" << std::dec;
        if (aliasOf)
            f << "  [shared/ICF body of " << aliasOf << "]";
        f << "\n";
    }
    f << "// [EXPORTS] found=" << found << " missing=" << missing
      << " aliased=" << aliased << " outside-module=" << outOfRange << "\n";
}

inline bool LookupTypeInfoRva(const DumpResult& r, const std::string& source, u32& out)
{
    for (auto& c : r.classes)
    {
        if (c.name != source && Qualified(c) != source) continue;
        if (c.ns.rfind("UnityEngine", 0) == 0 || c.ns.rfind("System", 0) == 0)
            continue;
        auto it = r.typeInfoRvas.find((u64)c.klass);
        if (it != r.typeInfoRvas.end() && !it->second.empty())
        {
            out = it->second.front();
            return true;
        }
    }
    return false;
}

inline void AppendRvaNamespace(std::ostream& f, const DumpResult& r)
{
    struct Rva { const char* alias; const char* source; u64 fallback; };
    // source is the class whose Il2CppClass slot is used; fallback is used only
    // when this dump could not find a slot for it (marked in the comment).
    static const Rva list[] = {
        { "BaseNetworkable",             "BaseNetworkableStatic", 0x111F0768 },
        { "BaseEntity",                  "BaseEntity",            0x1129D198 },
        { "BaseCombatEntity",            "BaseCombatEntity",      0x1129D170 },
        { "BasePlayer",                  "BasePlayer",            0x111FFDF0 },
        { "BaseNpc",                     "BaseNpc",               0x111FC768 },
        { "BaseVehicle",                 "BaseVehicle",           0x1120D288 },
        { "DroppedItemContainer",        "DroppedItemContainer",  0x111C0478 },
        { "OreResourceEntity",           "OreResourceEntity",     0x11253298 },
        { "CollectibleEntity",           "CollectibleEntity",     0x11253330 },
        { "BuildingBlock",               "BuildingBlock",         0x111A27D0 },
        { "BuildingPrivlidge",           "BuildingPrivlidge",     0x111E7600 },
        { "Door",                        "Door",                  0x111D3A40 },
        { "WorldItem",                   "WorldItem",             0x111BEDB0 },
        { "Signage",                     "Signage",               0x11183B28 },
        { "MainCamera",                  "MainCamera",            0x111C43A0 },
        { "ListComponent_Projectile",    "ListComponent<Projectile>", 0x11204AF0 },
        { "PlayerEyes",                  "PlayerEyes",            0x111C00E0 },
        { "PlayerModel",                 "PlayerModel",           0x111851B0 },
        { "TOD_Sky",                     "TOD_Sky",               0x11235250 },
        { "Item",                        "Item",                  0x11282E80 },
        { "ConsoleSystem_Command",       "ConsoleSystemCommand",  0x111AF278 },
        { "PlayerInventory_typenav",     "PlayerInventory",       0x111C2C80 },
        { "BaseNetworkable_TypeInfo",    "BaseNetworkableStatic", 0x111F0768 },
        { "BaseEntity_TypeInfo",         "BaseEntity",            0x1129D198 },
        { "BasePlayer_TypeInfo",         "BasePlayer",            0x111FFDF0 },
        { "PlayerEyes_TypeInfo",         "PlayerEyes",            0x111C00E0 },
        { "PlayerInventory_TypeInfo",    "PlayerInventory",       0x111C2C80 },
        { "PlayerModel_TypeInfo",        "PlayerModel",           0x111851B0 },
        { "PlayerInput_TypeInfo",        "PlayerInput",           0x1122D2A0 },
        { "BaseProjectile_TypeInfo",     "BaseProjectile",        0x11181BA8 },
        { "HeldEntity_TypeInfo",         "HeldEntity",            0x112957D0 },
        { "BaseViewModel_TypeInfo",      "BaseViewModel",         0x111F9500 },
        { "AutoTurret_TypeInfo",         "AutoTurret",            0x111E5910 },
        { "GameManager_Static_TypeInfo", "GameManagerStatic",     0x111FAE00 },
    };

    f << "namespace rva\n{\n";
    for (auto& e : list)
    {
        u32 rva = 0;
        // Only emit values the live dump actually proved. Hardcoded fallbacks
        // are not evidence and made the header look verified when it was not.
        if (!LookupTypeInfoRva(r, e.source, rva))
            continue;
        f << "    inline static constexpr std::uintptr_t " << e.alias
          << " = 0x" << std::hex << (u64)rva << std::dec << ";\n";
    }
    f << "} // namespace rva\n\n";
}

inline void WriteCombinedOffsetHeader(const DumpResult& r, const std::string& path,
    const std::string& cleanPath, const std::string& decryptPath)
{
    std::ofstream f(path, std::ios::binary);
    if (!f)
    {
        Log("[WRITE][!] cannot open %s", path.c_str());
        return;
    }
    Log("[WRITE] generating combined header: %s", path.c_str());

    const std::string cleanSrc = ReadWholeFile(cleanPath);
    const std::string decryptSrc = ReadWholeFile(decryptPath);

    std::string cleanBody;
    if (!ExtractBetween(cleanSrc, "namespace clean\n{", "} // namespace clean", cleanBody))
    {
        Log("[WRITE][!] offset.h: could not find namespace clean in %s", cleanPath.c_str());
        return;
    }

    // Pull the ready-made cipher functions out of decrypt.h so offset.h gets
    // actual callable implementations, not just RVAs.
    std::string decryptBody;
    {
        std::string open, close;
        size_t decPos = decryptSrc.find("namespace decryption");
        if (decPos != std::string::npos)
        {
            open = "namespace decryption";
            close = "} // namespace decryption";
        }
        else
        {
            decPos = decryptSrc.find("namespace decrypts");
            if (decPos != std::string::npos)
            {
                open = "namespace decrypts";
                close = "} // namespace decrypts";
            }
        }
        if (decPos != std::string::npos)
        {
            size_t body = decryptSrc.find('{', decPos + open.size());
            size_t end = decryptSrc.find(close, decPos);
            if (body != std::string::npos && end != std::string::npos && end > body)
                decryptBody = decryptSrc.substr(body + 1, end - body - 1);
        }
    }

    f << "// ============================================================================\n";
    f << "//  Rust-Offset-Dumper combined offsets - " << r.timestamp << "\n";
    f << "//  GameAssembly base at dump time: 0x" << std::hex << r.gameAssembly << std::dec << "\n";
    f << "//  Sections: EXPORTS -> namespace rva -> namespace offset -> namespace decrypt (ready fns)\n";
    f << "// ============================================================================\n\n";
    f << "#pragma once\n#include <cstddef>\n#include <cstdint>\n\n";

    AppendExportScan(f);
    f << "\n";

    AppendRvaNamespace(f, r);

    f << "namespace offset\n{";
    f << cleanBody;
    f << "} // namespace offset\n\n";

    f << "#ifndef RD_READ\n#define RD_READ(T, addr) (*reinterpret_cast<volatile T*>(addr))\n#endif\n";
    f << "#ifndef RD_GCHANDLE\n#define RD_GCHANDLE(x) (x)\n#endif\n\n";

    f << "namespace decrypt\n{\n";
    f << "    inline constexpr std::uint64_t client_entities_rva = 0x55A5C9D;\n";
    f << "    inline constexpr std::uint64_t entity_list_rva     = 0x1C5C550;\n";
    f << "    inline constexpr std::uint64_t local_player_rva    = 0x55A5C9D;\n";

    if (!decryptBody.empty())
    {
        f << decryptBody;
    }
    else
    {
        f << "    // decrypt.h had no implementation body - check the dump output.\n";
    }
    f << "} // namespace decrypt\n\n";

    f.flush();
    f.close();
    LogFileWritten(path);
}

// ---------------------------------------------------------------------------
//  output: generated offsets header
// ---------------------------------------------------------------------------
inline void WriteOffsetsHeader(const DumpResult& r, const std::string& path)
{
    std::ofstream f(path, std::ios::binary);
    if (!f)
    {
        Log("[WRITE][!] cannot open %s", path.c_str());
        return;
    }

    Log("[WRITE] generating offset header: %s", path.c_str());
    f << "// ============================================================================\n";
    f << "//  Rust-Offset-Dumper generated offsets - build detected live\n";
    f << "//  generated: " << r.timestamp << "\n";
    f << "//  GameAssembly base: 0x" << std::hex << r.gameAssembly << std::dec << "\n";
    f << "//  classes: " << r.classes.size() << "   typeinfo mappings: " << r.typeInfoRvas.size() << "\n";
    f << "//  every named instance field is exported; a slot with no readable name\n";
    f << "//  after the live metadata, the community table and revers/rev_binary.py is\n";
    f << "//  omitted (no field_0x placeholders).\n";
    f << "//  [live]  = measured with il2cpp_field_get_offset\n";
    f << "//  [live+table] = that value also matches the verified .rdata offset table\n";
    f << "//  [table] = recovered from that table (live accessor had no usable value)\n";
    f << "// ============================================================================\n\n";
    f << "#pragma once\n#include <cstddef>\n#include <cstdint>\n\n";
    f << "namespace offsets\n{\n";

    std::vector<const ClassRow*> sorted;
    for (auto& c : r.classes)
    {
        if (c.fields.empty()) continue;
        if (IsHashedIdent(c.name) || ContainsHashToken(c.name)) continue;
        if (IsCompilerGeneratedName(c.name)) continue;
        sorted.push_back(&c);
    }
    std::sort(sorted.begin(), sorted.end(), [](const ClassRow* a, const ClassRow* b) {
        if (a->name != b->name) return a->name < b->name;
        return a->ns < b->ns;
        });

    std::set<std::string> usedNs;
    for (auto* c : sorted)
    {
        std::string ns = SanitizeIdent(c->name);
        std::string uniq = ns;
        int n = 1;
        while (usedNs.count(uniq))
            uniq = ns + "_" + std::to_string(++n);
        usedNs.insert(uniq);

        f << "    // " << Qualified(*c) << "  klass=0x" << std::hex << (u64)c->klass << std::dec << "\n";
        f << "    namespace " << uniq << "\n    {\n";

        std::set<std::string> usedFields;
        size_t emittedFields = 0;
        for (auto& fr : c->fields)
        {
            // Only named slots are exported.  A name now comes from the live
            // metadata, the community table or revers/rev_binary.py; a slot that
            // is still an EAC hash after all three has no name to write, so it is
            // omitted instead of leaking a `field_0xNNN` placeholder.
            if (IsHashedIdent(fr.name) || ContainsHashToken(fr.name)) continue;
            if (IsCompilerGeneratedName(fr.name)) continue;
            std::string fn = SanitizeIdent(fr.name);
            std::string base = fn;
            int k = 1;
            while (usedFields.count(fn))
                fn = base + "_" + std::to_string(++k);
            usedFields.insert(fn);

            f << "        inline constexpr std::size_t " << fn << " = 0x"
              << std::hex << fr.offset << std::dec << ";";
            if (fr.flags & 0x10) f << " // static";
            else if (fr.evidence == 2) f << " // instance [live+table]";
            else if (fr.evidence == 3) f << " // instance [table]";
            else f << " // instance [live]";
            if (fr.name != fn) f << "  [" << fr.name << "]";
            f << "\n";
            ++emittedFields;
        }
        f << "    }\n\n";
        (void)emittedFields;
    }
    f << "} // namespace offsets\n";
    f.flush();
    f.close();
    LogFileWritten(path);
}

// ---------------------------------------------------------------------------
//  output: typeinfos
// ---------------------------------------------------------------------------
inline void WriteTypeInfos(const DumpResult& r, const std::string& path)
{
    std::ofstream f(path, std::ios::binary);
    if (!f)
    {
        Log("[WRITE][!] cannot open %s", path.c_str());
        return;
    }
    Log("[WRITE] generating typeinfo map: %s", path.c_str());
    f << "// Rust-Offset-Dumper typeinfo map - " << r.timestamp << "\n";
    f << "// typeinfo RVA is the GameAssembly data slot that holds the Il2CppClass*.\n";
    f << "// klasses without a slot are runtime-only (no cached TypeInfo in this build).\n\n";

    std::vector<const ClassRow*> sorted;
    for (auto& c : r.classes)
        sorted.push_back(&c);
    std::sort(sorted.begin(), sorted.end(), [](const ClassRow* a, const ClassRow* b) {
        return Qualified(*a) < Qualified(*b);
        });

    for (auto* c : sorted)
    {
        auto it = r.typeInfoRvas.find((u64)c->klass);
        if (it == r.typeInfoRvas.end())
            continue;
        f << "// " << Qualified(*c) << "\n";
        for (u32 rva : it->second)
            f << "inline constexpr std::size_t " << SanitizeIdent(c->name)
              << "_TypeInfo = 0x" << std::hex << rva << std::dec << ";\n";
        f << "\n";
    }
    f.flush();
    f.close();
    LogFileWritten(path);
}

// ---------------------------------------------------------------------------
//  output: class details for target classes
// ---------------------------------------------------------------------------
inline void WriteClassDetails(const DumpResult& r, const std::string& path)
{
    std::ofstream f(path, std::ios::binary);
    if (!f)
    {
        Log("[WRITE][!] cannot open %s", path.c_str());
        return;
    }
    Log("[WRITE] generating class details: %s", path.c_str());
    f << "// Rust-Offset-Dumper class detail - " << r.timestamp << "\n\n";

    std::vector<const ClassRow*> targets;
    for (auto& c : r.classes)
        if (c.target)
            targets.push_back(&c);
    std::sort(targets.begin(), targets.end(), [](const ClassRow* a, const ClassRow* b) {
        return Qualified(*a) < Qualified(*b);
        });

    for (auto* c : targets)
    {
        f << "============================================================================\n";
        f << "class " << Qualified(*c) << "\n";
        f << "  klass=0x" << std::hex << (u64)c->klass
          << "  parent=0x" << (u64)c->parent
          << "  static=0x" << c->staticData << std::dec << "\n";
        auto it = r.typeInfoRvas.find((u64)c->klass);
        if (it != r.typeInfoRvas.end())
        {
            f << "  typeinfo RVA:";
            for (u32 rva : it->second) f << " 0x" << std::hex << rva;
            f << std::dec << "\n";
        }
        else
            f << "  typeinfo RVA: <not found in data sections>\n";

        f << "  --- fields (" << c->fields.size() << ") ---\n";
        for (auto& fr : c->fields)
        {
            f << "  +0x" << std::hex << fr.offset << std::dec << "  "
              << (fr.flags & 0x10 ? "static  " : "instance") << "  "
              << fr.name;
            if (!fr.typeName.empty()) f << "  : " << fr.typeName;
            if (!fr.rawName.empty() && fr.rawName[0] == '%' && fr.rawName != fr.name)
                f << "   [" << fr.rawName << "]";
            f << "\n";
        }

        if (c->staticData)
        {
            f << "  --- static values ---\n";
            for (auto& fr : c->fields)
            {
                if (!(fr.flags & 0x10) || !il2::field_static_get_value)
                    continue;
                u64 out = 0;
                if (!il2::SafeStaticGetValue((il2::Il2CppField*)fr.field, &out))
                {
                    f << "  static +0x" << std::hex << fr.offset << std::dec
                      << " " << fr.name << " = <fault>\n";
                    continue;
                }
                f << "  static +0x" << std::hex << fr.offset << std::dec
                  << " " << fr.name << " = 0x" << std::hex << out
                  << " (" << (i64)out << ")\n" << std::dec;
            }
        }

        if (!c->methods.empty())
        {
            f << "  --- methods (" << c->methods.size() << ") ---\n";
            for (auto& mr : c->methods)
            {
                f << "  " << mr.name << " argc=" << mr.argc
                  << " meta=0x" << std::hex << (u64)mr.method
                  << " code=0x" << mr.code
                  << " RVA=0x" << mr.rva << std::dec << "\n";
            }
        }
        f << "\n";
    }
    f.flush();
    f.close();
    LogFileWritten(path);
}

// ---------------------------------------------------------------------------
//  live field value dumps
// ---------------------------------------------------------------------------
inline void DumpObjectFields(std::ofstream& f, u64 obj, const char* label, bool healthFilterOnly = false)
{
    if (!obj || !MemReadable(obj, 8))
    {
        f << "  " << label << " <unreadable>\n";
        return;
    }

    u64 k = ReadPtr(obj);
    std::string kn = il2::KlassName((void*)k);
    f << "  " << label << " obj=0x" << std::hex << obj
      << " klass=0x" << k << " name='" << kn << "'\n" << std::dec;

    u64 cur = k;
    for (int depth = 0; depth < 16 && cur; ++depth)
    {
        std::string cn = il2::KlassName((void*)cur);
        std::string cns = il2::KlassNamespace((void*)cur);
        f << "    [" << depth << "] " << (cns.empty() ? "" : cns + "::") << cn
          << " klass=0x" << std::hex << cur << std::dec << "\n";

        void* iter = nullptr;
        int guard = 0;
        while (guard++ < 2048 && il2::class_get_fields)
        {
            il2::Il2CppField* fld = nullptr;
            if (!il2::SafeClassGetFields((il2::Il2CppClass*)cur, &iter, &fld))
                break;
            if (!fld || !MemReadable((u64)fld, 0x20))
                break;
            int flagsRaw = 0;
            il2::SafeFieldFlags(fld, &flagsRaw);
            u32 flags = (u32)flagsRaw;
            if (flags & 0x10)
                continue;
            std::string fn = il2::FieldName(fld);
            size_t safeOff = 0;
            if (!il2::SafeFieldOffset(fld, &safeOff))
                continue;
            u32 off = (u32)safeOff;
            fn = DeobfuscateFieldName(il2::KlassName((void*)cur), fn, off,
                                      il2::FieldTypeName(fld));
            if (fn.empty() || fn[0] == '%')
            {
                char nb[32];
                sprintf_s(nb, sizeof(nb), "field_0x%X", off);
                fn = nb;
            }

            bool interesting = !healthFilterOnly ||
                StrContainsI(fn, "health") || StrContainsI(fn, "hp") ||
                StrContainsI(fn, "life") || StrContainsI(fn, "inventory") ||
                StrContainsI(fn, "item") || StrContainsI(fn, "body") ||
                StrContainsI(fn, "capsule") || StrContainsI(fn, "eyes") ||
                StrContainsI(fn, "userid") || StrContainsI(fn, "displayname") ||
                StrContainsI(fn, "model");
            if (!interesting)
                continue;

            u64 raw = ReadU64(obj + off);
            f << "      +0x" << std::hex << off << std::dec << " " << fn
              << " = 0x" << std::hex << raw << std::dec
              << "  i32=" << (i32)(u32)raw
              << "  f32=" << ReadF32(obj + off);
            if (StrContainsI(fn, "health") || StrContainsI(fn, "hp") || StrContainsI(fn, "life"))
                f << "   <-- HEALTH CANDIDATE";
            if (raw > 0x10000 && MemReadable(raw, 8))
            {
                std::string on = il2::KlassName((void*)ReadPtr(raw));
                if (!on.empty()) f << "  -> '" << on << "'";
            }
            f << "\n";
        }
        cur = (u64)ResolveParent((void*)cur);
    }
}

// ---------------------------------------------------------------------------
//  entity chain probe
// ---------------------------------------------------------------------------
inline void ProbeEntityChain(DumpResult& r, const std::string& path)
{
    std::ofstream f(path, std::ios::binary);
    if (!f)
    {
        Log("[CHAIN][!] cannot open %s", path.c_str());
        return;
    }

    f << "// Rust-Offset-Dumper entity-chain probe - " << r.timestamp << "\n\n";
    Log("[CHAIN] probing BaseNetworkable static -> realm -> entity list");

    il2::Il2CppClass* bn = il2::FindClass("", "BaseNetworkable");
    if (!bn) bn = il2::FindClass("", "%7e25fe33472b4f1230b3f6965e7753edbbaec2");
    f << "BaseNetworkable klass = 0x" << std::hex << (u64)bn << std::dec << "\n";
    Log("[CHAIN] BaseNetworkable klass=0x%llX", (unsigned long long)bn);
    if (!bn)
    {
        f << "NOT FOUND - cannot probe entity chain\n";
        Log("[CHAIN][!] BaseNetworkable not found - no chain");
        return;
    }

    bool statOk = false;
    u64 stat = il2::SafeStaticFieldData(bn, &statOk);
    if (!stat)
    {
        // 26140533 splits BaseNetworkable's static storage into the sibling
        // BaseNetworkableStatic class (hashed name, parent Object).  Use its
        // already-enumerated static block as the probe host.
        for (const auto& c : r.classes)
        {
            if (c.name != "BaseNetworkableStatic")
                continue;
            stat = c.staticData;
            if (!stat)
                stat = il2::SafeStaticFieldData((il2::Il2CppClass*)c.klass, &statOk);
            if (stat)
            {
                f << "// static block via BaseNetworkableStatic klass=0x"
                  << std::hex << (u64)c.klass << std::dec << "\n";
                Log("[CHAIN] static block via BaseNetworkableStatic klass=0x%llX",
                    (unsigned long long)c.klass);
            }
            break;
        }
    }
    f << "static block = 0x" << std::hex << stat << std::dec << "\n\n";
    Log("[CHAIN] static block=0x%llX%s", (unsigned long long)stat,
        statOk ? "" : "  (static-field-data accessor faulted)");
    if (!stat || !MemReadable(stat, 0x100))
    {
        f << "static block unreadable\n";
        Log("[CHAIN][!] static block unreadable");
        return;
    }

    for (u32 off = 0x10; off <= 0x80; off += 8)
    {
        u64 raw = ReadPtr(stat + off);
        if (!raw)
            continue;

        f << "static+0x" << std::hex << off << std::dec << " = 0x"
          << std::hex << raw << std::dec;
        std::string rn = il2::KlassName((void*)ReadPtr(raw));
        if (!rn.empty()) f << "  (object '" << rn << "')";
        f << "\n";
        Log("[CHAIN] static+0x%X = 0x%llX %s%s", off, (unsigned long long)raw,
            rn.empty() ? "" : "-> object '", rn.c_str());

        if (MemReadable(raw, 0x40))
        {
            u8 flag = 0; SafeRead(raw + 0x10, flag);
            u64 enc = ReadU64(raw + 0x18);
            u64 extra = ReadU64(raw + 0x20);
            f << "    wrapper: +0x10 flag=" << (int)flag
              << "  +0x18 enc=0x" << std::hex << enc
              << "  +0x20=0x" << extra << std::dec << "\n";
            Log("[CHAIN]   wrapper flag=%d enc=0x%llX extra=0x%llX",
                (int)flag, (unsigned long long)enc, (unsigned long long)extra);

            if (flag)
            {
                u64 ce = ClientEntitiesDecrypt(raw);
                u64 el = EntityListDecrypt(raw);
                f << "    client_entities_decrypt -> 0x" << std::hex << ce << std::dec;
                if (ce && MemReadable(ce, 0x30))
                {
                    std::string cn = il2::KlassName((void*)ReadPtr(ce));
                    if (!cn.empty()) f << "  klass='" << cn << "'";
                }
                f << "\n    entity_list_decrypt     -> 0x" << std::hex << el << std::dec;
                if (el && MemReadable(el, 0x30))
                {
                    std::string cn = il2::KlassName((void*)ReadPtr(el));
                    if (!cn.empty()) f << "  klass='" << cn << "'";
                }
                f << std::dec << "\n";
                Log("[CHAIN]   client_entities_decrypt=0x%llX  entity_list_decrypt=0x%llX",
                    (unsigned long long)ce, (unsigned long long)el);

                for (auto pair : { std::make_pair("client_entities", ce), std::make_pair("entity_list", el) })
                {
                    u64 v = pair.second;
                    if (!v || !MemReadable(v, 0x30)) continue;

                    u64 h = ResolveHandle(v);
                    if (h) v = h;

                    u32 cnt = 0;
                    if (LooksLikeEntityList(v, &cnt))
                    {
                        f << "    " << pair.first << " resolved LIST count=" << cnt << "\n";
                        Log("[CHAIN]   %s resolved LIST count=%u", pair.first, cnt);
                    }
                    else if (LooksLikeEntityArray(v, &cnt))
                    {
                        f << "    " << pair.first << " resolved ARRAY len=" << cnt << "\n";
                        Log("[CHAIN]   %s resolved ARRAY len=%u", pair.first, cnt);
                    }
                    else
                    {
                        f << "    " << pair.first << " resolved object, no list shape\n";
                        Log("[CHAIN]   %s resolved object, no list shape", pair.first);
                    }

                    std::string vn = il2::KlassName((void*)ReadPtr(v));
                    f << "      resolved klass='" << vn << "'\n";
                    if (MemReadable(v, 0x100))
                    {
                        for (u32 q = 0x10; q <= 0x80; q += 8)
                            f << "      +0x" << std::hex << q << " = 0x" << ReadPtr(v + q) << std::dec << "\n";
                    }
                }
            }
        }
    }
    f.flush();
    f.close();
    LogFileWritten(path);
}

// ---------------------------------------------------------------------------
//  camera matrix probe
// ---------------------------------------------------------------------------
inline u64 FindClassAnywhere(const char* name)
{
    // Unity engine types must be looked up in UnityEngine first - Assembly-CSharp
    // has its own unrelated "Camera" class and class_from_name walks assemblies
    // in load order.
    il2::Il2CppClass* k = il2::FindClass("UnityEngine", name);
    if (k) return (u64)k;
    k = il2::FindClass("", name);
    return (u64)k;
}

inline void ProbeCameras(const DumpResult& r, const std::string& path)
{
    std::ofstream f(path, std::ios::binary);
    if (!f)
    {
        Log("[CAM][!] cannot open %s", path.c_str());
        return;
    }

    f << "// Rust-Offset-Dumper camera probe - " << r.timestamp << "\n\n";
    Log("[CAM] probing UnityEngine.Camera objects");

    il2::Il2CppClass* camK = (il2::Il2CppClass*)FindClassAnywhere("Camera");
    f << "UnityEngine.Camera klass=0x" << std::hex << (u64)camK << std::dec << "\n";
    Log("[CAM] UnityEngine.Camera klass=0x%llX", (unsigned long long)camK);
    if (!camK)
    {
        Log("[CAM][!] Camera class not found");
        return;
    }

    u32 len = 0;
    const char* why = "";
    int ovl = 0;
    u64 arr = il2::FindObjectsOfType(camK, &len, &why, &ovl);
    f << "FindObjectsOfType -> arr=0x" << std::hex << arr << std::dec << " len=" << len
      << " overload(argc)=" << ovl << "\n\n";
    Log("[CAM] FindObjectsOfType -> arr=0x%llX len=%u overload(argc)=%d%s%s", 
        (unsigned long long)arr, len, ovl,
        arr ? "" : "  reason: ", arr ? "" : (why && *why ? why : "unknown"));
    if (!arr) return;

    for (u32 i = 0; i < len && i < 32; ++i)
    {
        u64 obj = ReadPtr(arr + 0x20 + i * 8);
        if (!obj || !MemReadable(obj, 0x30)) continue;
        u64 native = ReadPtr(obj + 0x10);
        f << "camera[" << i << "] obj=0x" << std::hex << obj << " native=0x" << native << std::dec << "\n";
        Log("[CAM] camera[%u] obj=0x%llX native=0x%llX", i,
            (unsigned long long)obj, (unsigned long long)native);

        for (u32 moff : { 0xB0u, 0x130u, 0x2FCu, 0x30Cu })
        {
            if (!native || !MemReadable(native + moff, 0x40)) continue;
            f << "  native+0x" << std::hex << moff << std::dec << ":\n";
            const float* m = (const float*)(native + moff);
            for (int row = 0; row < 4; ++row)
            {
                f << "    |";
                for (int col = 0; col < 4; ++col)
                {
                    char b[32];
                    sprintf_s(b, sizeof(b), "%10.5f", m[row * 4 + col]);
                    f << b << " ";
                }
                f << "|\n";
            }
            Log("[CAM]   native+0x%X row0 = %8.4f %8.4f %8.4f %8.4f", moff,
                m[0], m[1], m[2], m[3]);
            Log("[CAM]   native+0x%X row1 = %8.4f %8.4f %8.4f %8.4f", moff,
                m[4], m[5], m[6], m[7]);
            Log("[CAM]   native+0x%X row3 = %8.4f %8.4f %8.4f %8.4f", moff,
                m[12], m[13], m[14], m[15]);
        }
        f << "\n";
    }
    f.flush();
    f.close();
    LogFileWritten(path);
}

// ---------------------------------------------------------------------------
//  base player / dropped container live probe
// ---------------------------------------------------------------------------
inline void ProbeEntities(DumpResult& r, const std::string& path)
{
    std::ofstream f(path, std::ios::binary);
    if (!f)
    {
        Log("[LIVE][!] cannot open %s", path.c_str());
        return;
    }

    f << "// Rust-Offset-Dumper live entity probe - " << r.timestamp << "\n\n";
    Log("[LIVE] probing live entity instances");

    struct Target { const char* cls; const char* ns; bool healthOnly; int maxShow; };
    const Target targets[] = {
        { "BasePlayer", "", false, 40 },
        { "BaseCombatEntity", "", false, 8 },
        { "DroppedItemContainer", "", false, 30 },
        { "DroppedItem", "", false, 10 },
        { "BaseNetworkable", "", false, 5 },
    };

    for (auto& t : targets)
    {
        il2::Il2CppClass* k = il2::FindClass(t.ns, t.cls);
        if (!k)
        {
            f << "== " << t.cls << " NOT FOUND ==\n\n";
            Log("[LIVE] %s NOT FOUND", t.cls);
            continue;
        }

        // make sure inheritance is ready
        bool initOk = il2::SafeRuntimeClassInit(k);
        if (!initOk && il2::runtime_class_init)
            Log("[LIVE][!] %s il2cpp_runtime_class_init faulted - probing anyway", t.cls);

        u32 len = 0;
        const char* why = "";
        int ovl = 0;
        u64 arr = il2::FindObjectsOfType(k, &len, &why, &ovl);
        f << "== " << t.cls << " klass=0x" << std::hex << (u64)k
          << std::dec << " count=" << len << " arr=0x" << std::hex << arr << std::dec
          << " overload(argc)=" << ovl << " ==\n";
        Log("[LIVE] %s klass=0x%llX count=%u arr=0x%llX overload(argc)=%d", t.cls,
            (unsigned long long)k, len, (unsigned long long)arr, ovl);

        if (!arr)
        {
            f << "  FindObjectsOfType failed: " << (why && *why ? why : "unknown")
              << " (class not a UnityEngine.Object, or runtime rejected it)\n\n";
            Log("[LIVE] %s FindObjectsOfType FAILED: %s", t.cls,
                why && *why ? why : "unknown");
            continue;
        }

        u32 shown = 0;
        for (u32 i = 0; i < len && (int)shown < t.maxShow; ++i)
        {
            u64 obj = ReadPtr(arr + 0x20 + i * 8);
            if (!obj || !MemReadable(obj, 8))
                continue;

            // only dump objects assignable to the requested class (array may
            // contain subclasses)
            u64 ok = ReadPtr(obj);
            bool assignable = false;
            u64 cur = ok;
            for (int d = 0; d < 24 && cur; ++d)
            {
                if (cur == (u64)k) { assignable = true; break; }
                cur = (u64)ResolveParent((void*)cur);
            }
            if (!assignable)
                continue;

            char label[64];
            sprintf_s(label, "%s[%u]", t.cls, i);
            DumpObjectFields(f, obj, label, t.healthOnly);
            f << "\n";
            shown++;
        }
        f << "  shown " << shown << " of " << len << "\n\n";
        Log("[LIVE] %s shown %u of %u", t.cls, shown, len);
    }
    f.flush();
    f.close();
    LogFileWritten(path);
}

// ---------------------------------------------------------------------------
//  keyword index over *all* classes - finds health/inventory/decrypt fields
//  even when the class name is obfuscated
// ---------------------------------------------------------------------------
inline void WriteKeywordIndex(const DumpResult& r, const std::string& path)
{
    std::ofstream f(path, std::ios::binary);
    if (!f)
    {
        Log("[WRITE][!] cannot open %s", path.c_str());
        return;
    }
    Log("[WRITE] generating keyword index: %s", path.c_str());
    f << "// Rust-Offset-Dumper keyword index - " << r.timestamp << "\n";
    f << "// every field whose NAME matches a gameplay keyword, across all classes.\n\n";

    const char* keys[] = {
        "health", "hp", "life", "inventory", "item", "belt", "wear",
        "decrypt", "encrypt", "cliententit", "entitylist", "entitylist",
        "body", "capsule", "collider", "eyes", "model", "movement",
        "userid", "displayname", "team", "fov", "admin", "time", "sky",
        "position", "rotation", "velocity", "projectile", "damage"
    };

    for (auto& c : r.classes)
    {
        if (c.fields.empty())
            continue;

        std::vector<const FieldRow*> hits;        for (auto& fr : c.fields)
        {
            for (auto k : keys)
            {
                if (StrContainsI(fr.name, k))
                {
                    hits.push_back(&fr);
                    break;
                }
            }
        }
        if (hits.empty())
            continue;

        f << Qualified(c) << "  klass=0x" << std::hex << (u64)c.klass << std::dec << "\n";
        for (auto* fr : hits)
            f << "  +0x" << std::hex << fr->offset << std::dec << "  "
              << (fr->flags & 0x10 ? "static  " : "instance") << "  " << fr->name << "\n";
        f << "\n";
    }
    f.flush();
    f.close();
    LogFileWritten(path);
}

// ---------------------------------------------------------------------------
//  verified offset resolution (ported from the Vlone source)
//  included here because it needs Log(), DumpResult and ClassRow
// ---------------------------------------------------------------------------
#include "Resolver.h"

// ---------------------------------------------------------------------------
//  main dump entry
// ---------------------------------------------------------------------------
inline std::string TimestampNow()
{
    time_t t = time(nullptr);
    tm lt{};
    localtime_s(&lt, &t);
    char b[64];
    sprintf_s(b, "%04d-%02d-%02d %02d:%02d:%02d",
        lt.tm_year + 1900, lt.tm_mon + 1, lt.tm_mday,
        lt.tm_hour, lt.tm_min, lt.tm_sec);
    return b;
}

inline void RunDump(const char* why)
{
    DWORD t0 = GetTickCount();
    Log("============================================================");
    Log("[RUN] Rust-Offset-Dumper start (%s) - %s", why ? why : "-", TimestampNow().c_str());
    Log("[RUN] pid=%lu tid=%lu", GetCurrentProcessId(), GetCurrentThreadId());
    Log("[RUN] output dir = %s", g_outDir.c_str());
    LoadHashNames();

    char exe[MAX_PATH]{};
    GetModuleFileNameA(nullptr, exe, MAX_PATH);
    Log("[RUN] host exe = %s", exe);

    DumpResult r;
    r.timestamp = TimestampNow();
    r.gameAssembly = GetGameAssemblyBase();
    if (!r.gameAssembly)
    {
        Log("[!] GameAssembly.dll not found in this process");
        return;
    }
    r.imageSize = GetPeSizeOfImage(r.gameAssembly);
    Log("[+] GameAssembly = 0x%llX  SizeOfImage=0x%llX",
        (unsigned long long)r.gameAssembly, (unsigned long long)r.imageSize);
    if (!r.imageSize)
        Log("[!] SizeOfImage is 0 - the PE header was unreadable; RVA math will be unreliable");
    Log("[+] module range = 0x%llX..0x%llX",
        (unsigned long long)r.gameAssembly,
        (unsigned long long)(r.gameAssembly + r.imageSize));

    DWORD tExport = GetTickCount();
    Log("[STAGE] resolving IL2CPP exports...");
    if (!il2::ResolveExports(r.gameAssembly))
    {
        Log("[!] IL2CPP export resolution failed");
        LogExportStatus();
        return;
    }
    tExport = GetTickCount() - tExport;
    Log("[STAGE] IL2CPP exports resolved in %lu ms", tExport);
    LogExportStatus();

    // Proof that the generated decryptor chains belong to this exact binary.
    // tools/reverse.py hashed the first 64 bytes of every cipher block it
    // symbolically executed; a new game build changes those bytes and this
    // check fails instead of the dumper silently decrypting garbage.
    {
        std::string decReport;
        bool decOk = VerifyGeneratedDecryptors(r.gameAssembly, &decReport);
        Log("[DECRYPT] generated chains vs live GameAssembly: %s", decOk ? "ALL VERIFIED" : "MISMATCH");
        std::istringstream decLines(decReport);
        std::string decLine;
        while (std::getline(decLines, decLine))
            Log("%s", decLine.c_str());
        if (!decOk)
            Log("[DECRYPT][!] re-run: py tools/reverse.py   (header: src/generated/Decryptors.generated.h)");
    }

    Log("[STAGE] enumerating classes/fields/methods...");
    DWORD tEnum = GetTickCount();
    if (!EnumerateClasses(r))
    {
        Log("[!] class enumeration failed");
        return;
    }
    tEnum = GetTickCount() - tEnum;
    Log("[STAGE] class enumeration done in %lu ms", tEnum);

    Log("[STAGE] locating .rdata field-offset tables (static verification)...");
    DWORD tStatic = GetTickCount();
    ApplyStaticTables(r);
    tStatic = GetTickCount() - tStatic;
    Log("[STAGE] static offset tables done in %lu ms", tStatic);

    Log("[STAGE] scanning GameAssembly for TypeInfo slots...");
    DWORD tScan = GetTickCount();
    ScanTypeInfos(r);
    tScan = GetTickCount() - tScan;
    Log("[STAGE] typeinfo scan done in %lu ms", tScan);

    // ---- verified resolution: validate slots, prove the chain, sweep statics --
    Log("[STAGE] validating typeinfo slots + static blocks...");
    DWORD tRes = GetTickCount();
    std::vector<res::ResolvedSlot> slotInfo;
    res::ResolveSlots(r, slotInfo);

    Log("[STAGE] verifying live entity chain...");
    res::ChainHit chain;
    res::LocateEntityChain(r, chain);

    Log("[STAGE] sweeping static collections...");
    std::vector<res::SweepHit> sweep;
    res::SweepCollections(r, sweep, 20000);
    tRes = GetTickCount() - tRes;
    Log("[STAGE] verified resolution done in %lu ms", tRes);

    DWORD tWrite = GetTickCount();
    DWORD tProbe = 0;
    if (!g_outDir.empty())
    {
        Log("[STAGE] writing dump files...");
        WriteOffsetsHeader(r, g_outDir + "\\Rust-Offset-Dumper_offsets.h");
        WriteCleanOffsets(r, g_outDir + "\\Rust-Offset-Dumper_offsets_clean.h");
        WriteDecryptsHeader(r, g_outDir + "\\decrypt.h");
        WriteCombinedOffsetHeader(r, g_outDir + "\\offset.h",
            g_outDir + "\\Rust-Offset-Dumper_offsets_clean.h",
            g_outDir + "\\decrypt.h");
        WriteTypeInfos(r, g_outDir + "\\Rust-Offset-Dumper_typeinfos.txt");
        WriteClassDetails(r, g_outDir + "\\Rust-Offset-Dumper_classes.txt");
        WriteKeywordIndex(r, g_outDir + "\\Rust-Offset-Dumper_keywords.txt");
        WriteHashNameTable(g_outDir + "\\Rust-Offset-Dumper_hash_names.txt");
        res::WriteResolved(r, slotInfo, chain, sweep, g_outDir + "\\Rust-Offset-Dumper_resolved.h");
        tWrite = GetTickCount() - tWrite;

        Log("[STAGE] live probes...");
        DWORD tP = GetTickCount();
        ProbeEntityChain(r, g_outDir + "\\Rust-Offset-Dumper_entity_chain.txt");
        ProbeCameras(r, g_outDir + "\\Rust-Offset-Dumper_camera.txt");
        ProbeEntities(r, g_outDir + "\\Rust-Offset-Dumper_entities.txt");
        tProbe = GetTickCount() - tP;
        Log("[STAGE] live probes done in %lu ms", tProbe);

        Log("[+] files written to %s", g_outDir.c_str());
        Log("    Rust-Offset-Dumper_offsets.h      - generated offset header");
        Log("    Rust-Offset-Dumper_offsets_clean.h - named offsets + named typeinfo RVAs (no hashes)");
        Log("    decrypt.h                 - verified decryptors (client_entities, entity_list, ...)");
        Log("    offset.h                  - EXPORTS + namespace offset + namespace decrypt + decrypt impl");
        Log("    Rust-Offset-Dumper_typeinfos.txt  - klass -> typeinfo RVA");
        Log("    Rust-Offset-Dumper_classes.txt    - target class layouts + methods");
        Log("    Rust-Offset-Dumper_keywords.txt   - health/inventory/decrypt field index");
        Log("    Rust-Offset-Dumper_resolved.h     - VERIFIED typeinfo + entity chain + sweep");
        Log("    Rust-Offset-Dumper_entity_chain.txt - live realm/list probe");
        Log("    Rust-Offset-Dumper_camera.txt     - live camera matrices");
        Log("    Rust-Offset-Dumper_entities.txt   - live player/container field values");
        Log("    Rust-Offset-Dumper_hash_names.txt - hash -> name table (edit it, re-run, names apply)");
        Log("[HASH] resolved %zu use(s), %zu unresolved token(s) (%zu unique). "
            "Edit the table to name them.", g_hashHits, g_hashMisses, g_hashContext.size());
    }
    else
        Log("[WRITE][!] output directory is empty - no files written");

    const DWORD total = GetTickCount() - t0;
    Log("------------------------------------------------------------");
    Log("[SUMMARY] stage timings");
    Log("[SUMMARY]   exports         %6lu ms", tExport);
    Log("[SUMMARY]   enumeration     %6lu ms  (%zu classes, %zu fields, %zu methods)",
        tEnum, r.classes.size(),
        [&] { size_t n = 0; for (auto& c : r.classes) n += c.fields.size(); return n; }(),
        [&] { size_t n = 0; for (auto& c : r.classes) n += c.methods.size(); return n; }());
    Log("[SUMMARY]   typeinfo scan   %6lu ms  (%zu klass mapped)",
        tScan, r.typeInfoRvas.size());
    Log("[SUMMARY]   verification    %6lu ms  (%zu slot(s), chain=%s, sweep=%zu)",
        tRes, slotInfo.size(), chain.found ? "found" : "none", sweep.size());
    Log("[SUMMARY]   file writing    %6lu ms", tWrite);
    Log("[SUMMARY]   live probes     %6lu ms", tProbe);
    Log("[SUMMARY]   total           %6lu ms", total);

    PROCESS_MEMORY_COUNTERS pmc{};
    if (GetProcessMemoryInfo(GetCurrentProcess(), &pmc, sizeof(pmc)))
        Log("[SUMMARY] process working set = %.1f MB, peak = %.1f MB",
            pmc.WorkingSetSize / (1024.0 * 1024.0),
            pmc.PeakWorkingSetSize / (1024.0 * 1024.0));
    Log("------------------------------------------------------------");

    Log("[RUN] Rust-Offset-Dumper done - %s (total %lu ms)", TimestampNow().c_str(), total);
    Log("============================================================");
}
