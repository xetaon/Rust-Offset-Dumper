import struct
d = open(r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll", "rb").read()
pat = struct.pack("<I", 0x67676767)
i = 0
hits = []
while True:
    i = d.find(pat, i)
    if i == -1:
        break
    hits.append(i)
    i += 1
print("total dword hits", len(hits))
SECS = [(0x400, 0x8e4400, "text"), (0x8e4800, 0xe2ce600, "il2cpp"),
        (0xebb2e00, 0x20c6800, "rdata"), (0x10c79600, 0xa45e00, "data"),
        (0x116bf400, 0x82c800, "pdata")]
def sec(o):
    for raw, sz, n in SECS:
        if raw <= o < raw + sz:
            return n
    return "?"
from collections import Counter
c = Counter(sec(o) for o in hits)
print(c)
# show code hits context
codehits = [o for o in hits if sec(o) in ("text", "il2cpp")]
print("code hits", len(codehits), [hex(x) for x in codehits[:20]])
for o in codehits[:10]:
    raw, sz, n = next(x for x in SECS if x[2] == sec(o))
    va = (0x1000 if n == "text" else 0x8e6000) + (o - raw)
    print("off 0x%X va 0x%X ctx %s" % (o, va, d[o - 16:o + 20].hex()))
