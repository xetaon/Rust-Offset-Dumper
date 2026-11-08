import io, re
p = r"C:\Users\SystemX\Desktop\SteamAccGen\SteamAccGen.py"
s = io.open(p, encoding="utf-8").read()
checks = {
    "show_proxy_setting": "def show_proxy_setting" in s,
    "parse_proxy": "def parse_proxy" in s,
    "ProxyRelay": "class ProxyRelay" in s,
    "pick_proxy": "def pick_proxy" in s,
    "no_cyr_mojibake": "РЎ" not in s,
    "settings_9": '(9, f"Proxy:' in s,
    "settings_10": '"Proxy settings: "' in s,
    "proxy_in_launch": "--proxy-server=" in s,
    "relay_kill": "proxy_relay" in s,
    "auto_refresh": "refresh_auto_proxies()" in s,
}
for k, v in checks.items():
    print(f"{k:20} {v}")
print("lines", s.count("\n") + 1)
# any remaining replacement chars
print("replacement chars", s.count("\ufffd"))
