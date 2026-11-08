import json, urllib.request

H = {"User-Agent": "GalaxyClinic"}

def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=30).read().decode("utf-8", "replace")

base = "https://raw.githubusercontent.com/NtReadVirtualMemory/Roblox-Offsets-Website/main/"
for f in ["version", "offsets.json", "internal-offsets.hpp"]:
    print("\n=====", f, "=====")
    try:
        data = get(base + f)
        print(data[:12000])
    except Exception as e:
        print("FAIL", e)
