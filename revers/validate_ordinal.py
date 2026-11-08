import sys, re, struct, collections
sys.path.insert(0, r"C:\Users\SystemX\AppData\Local\Temp\opencode")
import meta_parse as M

d = M.d
N_OFF, N_SIZE, N_CNT = M.SEC["nestedTypes"]
# build child -> parent using each type's nestedTypesStart/count
def read_type(i):
    b = M.T_OFF + i*82
    return b
children = {}  # parent -> list
parent_of = {}
for i in range(M.NT):
    t = M.read_type(i)
    # re-read nested start/count
    b = M.T_OFF + i*82
    nestedStart = struct.unpack_from("<i", d, b+42)[0]
    nestedCount = struct.unpack_from("<H", d, b+66)[0]
    if nestedCount and nestedStart >= 0:
        for k in range(nestedCount):
            ch = struct.unpack_from("<i", d, N_OFF + (nestedStart+k)*4)[0]
            parent_of[ch] = i
            children.setdefault(i, []).append(ch)

rx = re.compile(r'^<>c__DisplayClass(\d+)_0$')
stats = collections.Counter()
examples = []
for i in range(M.NT):
    t = M.read_type(i)
    nm = t["name"] or ""
    m = rx.match(nm)
    if not m: continue
    N = int(m.group(1))
    # find ultimate enclosing non-compiler type
    p = parent_of.get(i)
    chain = []
    while p is not None and M.read_type(p)["name"] and M.read_type(p)["name"].startswith("<"):
        chain.append(p); p = parent_of.get(p)
    if p is None: 
        stats["no_parent"] += 1
        continue
    P = M.read_type(p)
    if not (0 <= N < P["methodCount"]):
        stats["ordinal_oob"] += 1
        continue
    meth = M.read_method(P["firstMethod"] + N)
    # outer name from any lambda in this display class
    outer = None
    for mi in range(t["firstMethod"], t["firstMethod"]+t["methodCount"]):
        mm = M.read_method(mi)
        mo = re.match(r'^<(.*)>b__\d+$', mm["name"] or "")
        if mo: outer = mo.group(1); break
    if outer is None:
        stats["no_lambda_name"] += 1; continue
    if meth["name"] == outer:
        stats["MATCH"] += 1
    elif meth["name"] and meth["name"].startswith("%"):
        stats["method_hashed"] += 1
    else:
        stats["MISMATCH"] += 1
        if len(examples) < 15:
            examples.append((nm, P["name"], N, outer, meth["name"], hex(meth["token"])))
print(stats)
print("examples:")
for e in examples: print("  ", e)
# Specifically: display class 102 in ItemIcon
for i in range(M.NT):
    t = M.read_type(i)
    if t["name"] == "<>c__DisplayClass102_0":
        p = parent_of.get(i)
        print("DisplayClass102 parent", p, M.read_type(p)["name"] if p is not None else None,
              "parentmethod102", M.read_method(M.read_type(p)["firstMethod"]+102) if p is not None else None)
