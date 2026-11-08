import json, urllib.request

H = {"User-Agent": "GalaxyClinic"}

def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=30).read()

for path in [
    "https://api.github.com/users/imtheo-dev/repos?per_page=100",
    "https://api.github.com/search/repositories?q=RbxDumperV2&per_page=10",
    "https://api.github.com/search/repositories?q=luau+offsets+executor&per_page=15",
    "https://api.github.com/search/repositories?q=roblox+internal+executor+luau&per_page=15",
]:
    print("\n=====", path, "=====")
    try:
        data = json.loads(get(path))
        items = data if isinstance(data, list) else data.get("items", [])
        for it in items[:15]:
            print(it.get("full_name"), "|", it.get("description"), "|", it.get("default_branch"))
    except Exception as e:
        print("FAIL", e)
