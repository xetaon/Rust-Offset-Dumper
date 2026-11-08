import io
s = io.open(r"C:\Users\SystemX\Desktop\SteamAccGen\SteamAccGen.py", encoding="utf-8", errors="replace").read()
i = s.find('print_box("Proxy"')
print(repr(s[i:i+160]))
j = s.find('\u041f\u0440\u043e\u043a\u0441\u0438')
print("cyr found at", j)
print(repr(s[j-80:j+80]) if j > 0 else "none")
k = s.find("Chrome: direct connection")
print(repr(s[k-120:k+60]))
