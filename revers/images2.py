import hashlib, sys, struct
sys.path.insert(0, r"C:\Users\SystemX\AppData\Local\Temp\opencode")
import meta_parse as M

# correct image section (v39: no typeInlineArrays)
IMG_OFF, IMG_SIZE, IMG_CNT = 0x3f14cb8, 0x16c8, 162
def img(i):
    b = IMG_OFF + i*36
    nameIdx, asmIdx = struct.unpack_from("<ii", d, b) if False else struct.unpack_from("<ii", M.d, b)
    firstType = struct.unpack_from("<H", M.d, b+8)[0]
    typeCount = struct.unpack_from("<I", M.d, b+10)[0]
    return dict(i=i, name=M.st(nameIdx), asmIdx=asmIdx, firstType=firstType, typeCount=typeCount)

images = [img(i) for i in range(IMG_CNT)]
print("first 5 images:", images[:5])
def img_of_type(ti):
    for im in images:
        if im["firstType"] <= ti < im["firstType"]+im["typeCount"]:
            return im
    return None
for tid in (24641, 6156, 2293, 12823, 5862, 7896, 8664, 3452, 8570, 289):
    im = img_of_type(tid)
    print("type", tid, M.read_type(tid)["name"], "-> image", im["i"], im["name"], "typeStart", im["firstType"], "count", im["typeCount"])

print("--- hash test ---")
for s in ["TryToMove","Update","Awake","PerformanceUI","CinematicEntity","ItemIcon","OnClicked","LateUpdate","DoAttack","ClientInput"]:
    for alg in ("sha1","sha256","md5"):
        h = hashlib.new(alg, s.encode()).hexdigest()
        if (alg=="sha256" and len(h)>40): h = h[:40]
        found = M.d.find(b"%"+h.encode())
        if found >= 0:
            print("MATCH", alg, s, "%"+h, "at", hex(found))
    print("sha1", s, hashlib.sha1(s.encode()).hexdigest())
