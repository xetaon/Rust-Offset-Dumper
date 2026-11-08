#include <windows.h>
#include <cstdio>
#include <string>

static void W(const char* path, const char* text)
{
    HANDLE h = CreateFileA(path, GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE,
        nullptr, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (h == INVALID_HANDLE_VALUE)
        return;
    DWORD wrote = 0;
    WriteFile(h, text, (DWORD)lstrlenA(text), &wrote, nullptr);
    FlushFileBuffers(h);
    CloseHandle(h);
}

static DWORD WINAPI Worker(LPVOID)
{
    char buf[512];
    wsprintfA(buf, "probe pid=%lu tick=%lu\r\n", GetCurrentProcessId(), GetTickCount());
    W("C:\\Users\\SystemX\\AppData\\Local\\Temp\\opencode\\probe_temp.txt", buf);
    W("C:\\Users\\SystemX\\Desktop\\Rust-Offset-DumperDumps\\probe_desktop.txt", buf);

    // CRT path as well
    FILE* f = nullptr;
    fopen_s(&f, "C:\\Users\\SystemX\\AppData\\Local\\Temp\\opencode\\probe_crt.txt", "w");
    if (f) { fprintf(f, "crt ok pid=%lu\r\n", GetCurrentProcessId()); fflush(f); fclose(f); }
    return 0;
}

BOOL APIENTRY DllMain(HMODULE h, DWORD r, LPVOID)
{
    if (r == DLL_PROCESS_ATTACH)
    {
        DisableThreadLibraryCalls(h);
        HANDLE t = CreateThread(nullptr, 0, Worker, nullptr, 0, nullptr);
        if (t) CloseHandle(t);
    }
    return TRUE;
}
