#include "Dumper.h"

// ============================================================================
//  Rust-Offset-Dumper / DllMain.cpp
//
//  Injected x64 DLL.  On attach it spawns a worker that:
//    1. waits for the IL2CPP runtime to be ready
//    2. enumerates every class/field/method from the LIVE metadata
//    3. finds each class's TypeInfo RVA by scanning GameAssembly data sections
//    4. probes entity chains, camera matrices and live player/container fields
//    5. writes everything next to the Desktop in Rust-Offset-DumperDumps\
//
//  Press F8 in-game at any time to re-run the dump.
//  You can also call the exported RustOffsetDumper_Run() from your injector.
// ============================================================================

static volatile LONG g_running = 0;
static volatile LONG g_dumpRequest = 0;
static HMODULE g_selfModule = nullptr;

static std::string DesktopDumpDir()
{
    char profile[MAX_PATH]{};
    DWORD n = GetEnvironmentVariableA("USERPROFILE", profile, MAX_PATH);
    if (!n || n >= MAX_PATH)
        return "C:\\Rust-Offset-DumperDumps";

    std::string dir = std::string(profile) + "\\Desktop\\Rust-Offset-DumperDumps";
    return dir;
}

static DWORD WINAPI WorkerThread(LPVOID)
{
    if (InterlockedCompareExchange(&g_running, 1, 0) != 0)
        return 0;

    std::string dir = DesktopDumpDir();
    LogInit(dir);
    Log("============================================================");
    Log("  Rust-Offset-Dumper  -  live IL2CPP offset / chain / decrypt dumper");
    Log("  build tag: 26140533 compatible");
    Log("  compiled:  " __DATE__ " " __TIME__);
    Log("============================================================");
    Log("[INIT] Rust-Offset-Dumper injected, pid=%lu tid=%lu",
        GetCurrentProcessId(), GetCurrentThreadId());
    Log("[INIT] output directory: %s", dir.c_str());

    char self[MAX_PATH]{};
    if (g_selfModule)
        GetModuleFileNameA(g_selfModule, self, MAX_PATH);
    Log("[INIT] dll path: %s", self[0] ? self : "<unknown>");

    Log("[INIT] waiting for GameAssembly + IL2CPP exports...");

    // Wait until GameAssembly is loaded and IL2CPP has classes.
    u64 base = 0;
    for (int i = 0; i < 600; ++i)
    {
        base = GetGameAssemblyBase();
        if (base)
        {
            HMODULE h = (HMODULE)base;
            if (GetProcAddress(h, "il2cpp_domain_get") &&
                GetProcAddress(h, "il2cpp_class_get_fields"))
            {
                Log("[INIT] IL2CPP ready after %d ms", (i + 1) * 100);
                break;
            }
        }
        if ((i % 20) == 0)
            Log("[WAIT] %d ms, GameAssembly=0x%llX", i * 100, (unsigned long long)base);
        Sleep(100);
    }

    if (!base)
    {
        Log("[!] GameAssembly.dll never appeared - aborting");
        LogClose();
        InterlockedExchange(&g_running, 0);
        return 0;
    }

    // Give the scene a moment to come up (local player, cameras, containers).
    Log("[INIT] waiting 4000 ms for the scene (player/cameras/containers)...");
    Sleep(4000);

    RunDump("auto: attached");

    Log("[HOTKEY] F8 = re-dump, END = stop worker (DLL stays loaded)");
    while (true)
    {
        if (InterlockedExchange(&g_dumpRequest, 0) != 0)
            RunDump("export request");

        if (GetAsyncKeyState(VK_F8) & 0x8000)
        {
            // debounce
            while (GetAsyncKeyState(VK_F8) & 0x8000)
                Sleep(30);
            RunDump("hotkey F8");
        }

        if (GetAsyncKeyState(VK_END) & 0x8000)
        {
            Log("[HOTKEY] END pressed - stopping dumper thread (DLL stays loaded)");
            break;
        }

        Sleep(80);
    }

    Log("[EXIT] worker stopped");
    LogClose();
    InterlockedExchange(&g_running, 0);
    return 0;
}

extern "C" __declspec(dllexport) void RustOffsetDumper_Run()
{
    InterlockedExchange(&g_dumpRequest, 1);
}

extern "C" __declspec(dllexport) const char* RustOffsetDumper_OutputDir()
{
    static std::string dir = DesktopDumpDir();
    return dir.c_str();
}

BOOL APIENTRY DllMain(HMODULE hModule, DWORD reason, LPVOID)
{
    if (reason == DLL_PROCESS_ATTACH)
    {
        g_selfModule = hModule;
        DisableThreadLibraryCalls(hModule);
        HANDLE h = CreateThread(nullptr, 0, WorkerThread, nullptr, 0, nullptr);
        if (h)
            CloseHandle(h);
    }
    else if (reason == DLL_PROCESS_DETACH)
    {
        Log("[EXIT] process detach");
        LogClose();
    }
    return TRUE;
}
