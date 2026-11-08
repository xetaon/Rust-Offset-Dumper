from pathlib import Path

p = Path(r"C:\Users\SystemX\Desktop\SteamAccGen\SteamAccGen.py")
s = p.read_text(encoding="utf-8")


def cut(text, start, end):
    i = text.index(start)
    j = text.index(end, i)
    print(f"cut {i}..{j}: {text[i:i+60]!r}")
    return text[:i] + text[j:]


s = cut(s, "# ==========================================================================\n#          PROXY STATE:", "def random_login(")
s = cut(s, "def ban_proxy(server, reason=\"\"):", "def register_one_account(")
s = cut(s, "def is_proxy_detected_error(text):", "def send_to_discord(")
s = cut(s, "def chrome_proxy_arg(server):", "def launch_chrome_with_cdp(")
s = cut(s, "def ensure_proxy_dependencies():", "def main():")

p.write_text(s, encoding="utf-8")
print("done")
