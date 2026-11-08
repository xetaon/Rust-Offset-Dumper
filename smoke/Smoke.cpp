#include "../src/Dumper.h"
int main()
{
    LogInit("C:\\Users\\SystemX\\AppData\\Local\\Temp\\opencode\\dumpersmoke");
    Log("[INIT] smoke pid=%lu", GetCurrentProcessId());
    Log("[INIT] second line %s", "ok");
    LogClose();
    return 0;
}
