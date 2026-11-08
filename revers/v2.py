import ast, io
p = r"C:\Users\SystemX\Desktop\SteamAccGen\SteamAccGen.py"
s = io.open(p, encoding="utf-8").read()
tree = ast.parse(s)
funcs = [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]
for name in ["fetch_country_codes", "_ip_from_info", "proxy_country",
             "is_russian_proxy", "_probe_proxy", "check_proxy", "pick_proxy",
             "refresh_auto_proxies"]:
    print(f"{name:22} count={funcs.count(name)}")
print("RU_ONLY =", "RU_ONLY = True" in s)
print("replacement chars:", s.count("\ufffd"))
print("mojibake:", "РЎ" in s)
