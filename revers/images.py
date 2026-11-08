import struct, sys
sys.path.insert(0, r"C:\Users\SystemX\AppData\Local\Temp\opencode")
import meta_parse as M
d = M.d
off, size, cnt = M.SEC["images"]
print("images", hex(off), hex(size), cnt, "size/cnt", size/cnt)
offa, sizea, cnta = M.SEC["assemblies"]
print("assemblies", hex(offa), hex(sizea), cnta, "size/cnt", sizea/cnta)
# image struct candidates
IS = size // cnt
print("image struct size", IS)
def img(i):
    b = off + i*IS
    nameIdx, asmIdx = struct.unpack_from("<ii", d, b)
    typeStart, typeCount = struct.unpack_from("<ii", d, b+8)
    expStart, expCount, entry, token = struct.unpack_from("<iiii", d, b+16)
    return dict(i=i, name=M.st(nameIdx), asmIdx=asmIdx, typeStart=typeStart, typeCount=typeCount, entry=entry, token=token)
for i in range(cnt):
    im = img(i)
    if im["typeStart"] <= 24641 < im["typeStart"]+im["typeCount"] or im["typeStart"] <= 6156 < im["typeStart"]+im["typeCount"]:
        print("IMAGE", im)
# all types named PerformanceUI
print("--- PerformanceUI types ---")
n = 0
for i in range(M.NT):
    t = M.read_type(i)
    if t["name"] == "PerformanceUI":
        print(i, t["ns"], hex(t["token"]), "firstMethod", t["firstMethod"], "count", t["methodCount"])
        n += 1
print("total", n)
# types with token 0x2000024
print("--- token 0x2000024 ---")
for i in range(M.NT):
    t = M.read_type(i)
    if t["token"] == 0x2000024:
        print(i, t["ns"], t["name"], t["firstMethod"], t["methodCount"])
# print types 0..40 names/tokens/firstMethod for context
print("--- first types ---")
for i in range(0, 45):
    t = M.read_type(i)
    print(i, t["ns"], t["name"], hex(t["token"]), t["firstMethod"], t["methodCount"])
