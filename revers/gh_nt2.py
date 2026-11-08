import urllib.request

H = {"User-Agent": "GalaxyClinic"}
base = "https://raw.githubusercontent.com/NtReadVirtualMemory/Roblox-Offsets-Website/main/"
for f in ["offsets.hpp", "offsets_structured.hpp", "Methods/DataModel_Using_VisualEnginePointer.cpp", "internal-offsets.hpp", "types.hpp"]:
    print("\n=====", f, "=====")
    try:
        data = urllib.request.urlopen(urllib.request.Request(base + f, headers=H), timeout=30).read().decode("utf-8", "replace")
        print(data[:8000])
        print("...LEN", len(data))
    except Exception as e:
        print("FAIL", e)
