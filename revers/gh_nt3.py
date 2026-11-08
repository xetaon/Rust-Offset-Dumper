import urllib.request, re

H = {"User-Agent": "GalaxyClinic"}
u = "https://raw.githubusercontent.com/NtReadVirtualMemory/Roblox-Offsets-Website/main/offsets_structured.hpp"
data = urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=30).read().decode("utf-8", "replace")

for kw in ["Pointer", "TaskScheduler", "ScriptContext", "VisualEngine", "GlobalState", "Luau", "Identity", "Jobs", "DataModel"]:
    print("\n====", kw, "====")
    for line in data.splitlines():
        if kw.lower() in line.lower():
            print(line)

print("\nTAIL:")
print(data[-2500:])
