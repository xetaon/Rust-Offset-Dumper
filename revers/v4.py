import ast, io, collections
p = r"C:\Users\SystemX\Desktop\SteamAccGen\SteamAccGen.py"
s = io.open(p, encoding="utf-8").read()
tree = ast.parse(s)
names = [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]
dups = [n for n, c in collections.Counter(names).items() if c > 1]
print("total funcs:", len(names))
print("dups:", dups)
print("lines:", s.count("\n") + 1)
print("proxy:", "proxy" in s.lower())
# check blank lines / trailing artifacts
print("triple blank:", s.count("\n\n\n\n"))
