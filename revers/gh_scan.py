import json, urllib.request

H = {"User-Agent": "GalaxyClinic"}


def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=30).read()


for repo in [
    "Sarshanin/Roblox-Dumper-actually-works-and-opensource-",
    "Lonegwadiwaitor/roblox-offset-dumper",
    "verlorenheit/paprod",
    "lordnikky/ida-offset-dumper",
]:
    try:
        meta = json.loads(get(f"https://api.github.com/repos/{repo}"))
        br = meta.get("default_branch", "main")
        tree = json.loads(get(f"https://api.github.com/repos/{repo}/git/trees/{br}?recursive=1"))
        print("====", repo, br, "====")
        for it in tree.get("tree", []):
            if it["type"] == "blob":
                print(it["path"])
    except Exception as e:
        print("FAIL", repo, e)
