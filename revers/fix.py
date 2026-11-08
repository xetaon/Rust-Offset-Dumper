import io, sys
p = r"C:\Users\SystemX\Desktop\SteamAccGen\SteamAccGen.py"
s = io.open(p, encoding="utf-8").read()
for enc in ("cp1252", "cp1251", "latin-1"):
    try:
        raw = s.encode(enc)
    except UnicodeEncodeError as e:
        print(enc, "ENCODE FAIL", e)
        continue
    try:
        fixed = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        print(enc, "DECODE FAIL", e)
        continue
    print(enc, "OK len", len(fixed),
          "cyr:", "\u041d\u0435\u0432\u0430\u043b\u0438\u0434\u043d\u044b\u0439 \u043f\u0440\u043e\u043a\u0441\u0438" in fixed)
    if "\u041d\u0435\u0432\u0430\u043b\u0438\u0434\u043d\u044b\u0439 \u043f\u0440\u043e\u043a\u0441\u0438" in fixed:
        io.open(p, "w", encoding="utf-8", newline="").write(fixed)
        print("written with", enc)
        break
