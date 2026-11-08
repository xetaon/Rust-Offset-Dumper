import json, urllib.request

H = {"User-Agent": "GalaxyClinic"}

def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=30).read()

for repo in ["certier/Aether", "meowpurrpur/RbxDumperV2"]:
    try:
        meta = json.loads(get(f"https://api.github.com/repos/{repo}"))
        br = meta.get("default_branch", "main")
        tree = json.loads(get(f"https://api.github.com/repos/{repo}/git/trees/{br}?recursive=1"))
        print("\n====", repo, br, "====")
        for it in tree.get("tree", []):
            if it["type"] == "blob":
                p = it["path"]
                if any(x in p.lower() for x in ["offset", "luau", "lua", "signature", "scanner", "executor", "inject"]):
                    print(p)
    except Exception as e:
        print("FAIL", repo, e)
