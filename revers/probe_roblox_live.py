import sys, math, collections
sys.path.insert(0, r"C:\Users\SystemX\Desktop\Galaxy.Clinic Executor\scripts")
from galaxy.winmem import open_process, ProcessMemoryError, enable_debug_privilege

enable_debug_privilege()
pid = 10264
try:
    with open_process(pid) as process:
        print("opened", pid)
        modules = process.modules()
        print("modules", len(modules))
        for module in modules[:10]:
            print(f"  {module.name} base=0x{module.base:X} size=0x{module.size:X}")
        module = process.module("RobloxPlayerBeta.exe") or process.main_module()
        print("main", module)
        if module:
            for offset in (0, 0x1000, 0x100000, 0x4000000):
                try:
                    chunk = process.read(module.base + offset, 4096)
                    counts = collections.Counter(chunk)
                    entropy = -sum((n/len(chunk))*math.log2(n/len(chunk)) for n in counts.values())
                    print(f"read +0x{offset:X}: {len(chunk)} entropy={entropy:.3f} head={chunk[:16].hex(' ')}")
                except ProcessMemoryError as exc:
                    print(f"read +0x{offset:X}: FAIL {exc}")
            # try strings in a readable region
            try:
                text = process.read(module.base + 0x600, 0x100000)
                for needle in (b"RSB1", b"cannot resume dead coroutine", b"Lua function expected"):
                    print(needle, text.find(needle))
            except ProcessMemoryError as exc:
                print("string read failed", exc)
except Exception as exc:
    print("ERROR", type(exc).__name__, exc)
