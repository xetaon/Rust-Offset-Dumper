import io
p = r"C:\Users\SystemX\Desktop\SteamAccGen\SteamAccGen.py"
s = io.open(p, encoding="utf-8").read()
start = s.index("BANNER = [")
end = s.index("]\n\nclass COORD", start) + 1
s = s[:start] + s[end:]
s = s.replace('BANNER_GRADIENT_START = (100, 60, 220)\nBANNER_GRADIENT_END = (60, 180, 255)\n', "")
io.open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")
