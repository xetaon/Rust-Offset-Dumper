import struct
DLL = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
data = open(DLL, "rb").read()
IB = 0x180000000
secs = [(".text", 0x1000, 0x8e4400, 0x400, 0x8e4400),
        ("il2cpp", 0x8e6000, 0xe2ce600, 0x8e4800, 0xe2ce600),
        (".rdata", 0xebb5000, 0x20c6800, 0xebb2e00, 0x20c6800),
        (".data", 0x10c7c000, 0xa45e00, 0x10c79600, 0xa45e00)]
def r2o(r):
    for n, va, vs, raw, rs in secs:
        if va <= r < va + rs:
            return raw + (r - va)
    return None
def o2r(o):
    for n, va, vs, raw, rs in secs:
        if raw <= o < raw + rs:
            return va + (o - raw)
    return None

TARGETS = {0xEBF22B0: "BasePlayer", 0xec2cb08: "Projectile", 0xec4c4d0: "AttackEntity"}

def probe(off, n=12, label=""):
    print("=== %s off=0x%X" % (label, off))
    for i in range(n):
        q = struct.unpack_from("<Q", data, off + i * 8)[0]
        r = q - IB if q >= IB else None
        print("  [%d] %#x rva=%s" % (i, q, hex(r) if r else "-"))
        if r in TARGETS:
            print("      ^^^ %s" % TARGETS[r])

probe(0x110EF100, 8, "data run F 0x110EF100")
probe(0xF0B0598, 8, "rdata run 0xF0B0598")
probe(0xFBA9B30, 8, "rdata run 0xFBA9B30")

# search these arrays for target pointers
for arr_off, ln in ((0x110EF100, 33457), (0xF0B0598, 25205), (0xFBA9B30, 92509),
                    (0x114F6180, 62621), (0x11570680, 38642), (0x114B8E70, 31326),
                    (0x1148D348, 22371)):
    found = []
    for i in range(ln):
        q = struct.unpack_from("<Q", data, arr_off + i * 8)[0]
        r = q - IB
        if r in TARGETS:
            found.append((i, TARGETS[r]))
    print("ARR 0x%X len=%d -> %s" % (arr_off, ln, found[:10]))
