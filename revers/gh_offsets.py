import json, urllib.request

H = {"User-Agent": "GalaxyClinic"}


def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=30).read().decode("utf-8", "replace")


base = "https://raw.githubusercontent.com/4anti/Roblox-Offsets-ALL/main/"
for f in ["endpoints/imtheo/meta.json", "endpoints/imtheo/FFlags.json", "endpoints/ntreadvirtualmemory/meta.json",
          "endpoints/souloveryall/meta.json", "endpoints/souloveryall/Offsets.hpp", "README.md"]:
    print("\n=====", f, "=====")
    try:
        print(get(base + f)[:4000])
    except Exception as e:
        print("FAIL", e)

for repo in ["NtReadVirtualMemory/Roblox-Offsets-Website"]:
    try:
        meta = json.loads(get(f"https://api.github.com/repos/{repo}"))
        br = meta["default_branch"]
        tree = json.loads(get(f"https://api.github.com/repos/{repo}/git/trees/{br}?recursive=1"))
        print("\n=====", repo, "=====")
        for it in tree["tree"]:
            if it["type"] == "blob":
                print(it["path"])
    except Exception as e:
        print("FAIL", repo, e)
