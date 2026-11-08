import io, sys
p = r"C:\Users\SystemX\Desktop\SteamAccGen\SteamAccGen.py"
s = io.open(p, encoding="utf-8").read()
out = bytearray()
bad = 0
for ch in s:
    cp = ord(ch)
    if cp < 256:
        out.append(cp)
        continue
    try:
        out += ch.encode("cp1251")
    except UnicodeEncodeError:
        bad += 1
        out += ch.encode("utf-8")
print("unmapped chars:", bad)
try:
    fixed = out.decode("utf-8")
except UnicodeDecodeError as e:
    print("DECODE FAIL", e)
    sys.exit(1)
print("len", len(fixed))
print("cyr ok:", "\u041d\u0435\u0432\u0430\u043b\u0438\u0434\u043d\u044b\u0439 \u043f\u0440\u043e\u043a\u0441\u0438" in fixed)
print("title ok:", "\u0423\u0421\u041a\u041e\u0420\u0415\u041d\u0418\u0415" in fixed)
io.open(p, "w", encoding="utf-8", newline="").write(fixed)
print("written")
