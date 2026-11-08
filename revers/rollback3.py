import io
p = r"C:\Users\SystemX\Desktop\SteamAccGen\SteamAccGen.py"
s = io.open(p, encoding="utf-8", newline="").read()
s = s.replace("\r\n", "\n").replace("\n", "\r\n")
with open(p, "wb") as f:
    f.write(s.encode("utf-8"))
print("crlf lines:", s.count("\r\n"))

ip = r"C:\Users\SystemX\Desktop\SteamAccGen\SteamAccGen.ini"
lines = io.open(ip, encoding="utf-8").read().splitlines()
keep = [ln for ln in lines if not ln.startswith(("proxy_enabled", "proxy_auto_parse", "proxy "))]
io.open(ip, "w", encoding="utf-8", newline="").write("\r\n".join(keep) + "\r\n")
print("ini cleaned")
