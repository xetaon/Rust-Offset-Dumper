import io
p = r"C:\Users\SystemX\Desktop\SteamAccGen\SteamAccGen.py"
s = io.open(p, encoding="utf-8").read()
start = s.index("def show_proxy_setting():")
end = s.index("def show_settings():")
print("cut chars:", end - start)
s = s[:start] + s[end:]
io.open(p, "w", encoding="utf-8", newline="").write(s)
print("done, lines:", s.count("\n") + 1)
