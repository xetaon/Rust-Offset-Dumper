import io
p = r"C:\Users\SystemX\Desktop\SteamAccGen\SteamAccGen.py"
s = io.open(p, encoding="utf-8").read()
print(repr(s[1150:1250]))
print([hex(ord(c)) for c in s[1175:1200]])
