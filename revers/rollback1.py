import io
p = r"C:\Users\SystemX\Desktop\SteamAccGen\SteamAccGen.py"
s = io.open(p, encoding="utf-8").read()
start = s.index("def parse_proxy(raw):")
end = s.index("def launch_chrome_with_cdp(profile_dir):")
print("cut chars:", end - start)
s = s[:start] + s[end:]
io.open(p, "w", encoding="utf-8", newline="").write(s)
print("done, lines:", s.count("\n") + 1)
