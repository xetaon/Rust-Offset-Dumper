import ast, io
p = r"C:\Users\SystemX\Desktop\SteamAccGen\SteamAccGen.py"
tree = ast.parse(io.open(p, encoding="utf-8").read())
names = {"PROXY_ENABLED", "PROXY_VALUE", "PROXY_AUTO_PARSE", "AUTO_PROXIES"}
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        assigned = set()
        for sub in ast.walk(node):
            if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Store):
                assigned.add(sub.id)
        hit = assigned & names
        if hit:
            decl = set()
            for sub in node.body:
                if isinstance(sub, ast.Global):
                    decl.update(sub.names)
            missing = hit - decl
            status = "OK" if not missing else "MISSING " + str(missing)
            print(f"{node.name:35} {status}")
