import sys, urllib.request

H = {"User-Agent": "GalaxyClinic"}
base = "https://raw.githubusercontent.com/Lonegwadiwaitor/roblox-offset-dumper/main/"
files = sys.argv[1:]
for f in files:
    print("\n" + "=" * 30 + " " + f + " " + "=" * 30)
    try:
        data = urllib.request.urlopen(urllib.request.Request(base + f, headers=H), timeout=30).read().decode("utf-8", "replace")
        print(data[:20000])
    except Exception as e:
        print("FAIL", e)
