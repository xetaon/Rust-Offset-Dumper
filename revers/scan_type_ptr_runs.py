import struct
DLL = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
data = open(DLL, "rb").read()
IB = 0x180000000
SECS = [(".text", 0x1000, 0x8e4400, 0x400, 0x8e4400),
        ("il2cpp", 0x8e6000, 0xe2ce600, 0x8e4800, 0xe2ce600),
        (".rdata", 0xebb5000, 0x20c6800, 0xebb2e00, 0x20c6800),
        (".data", 0x10c7c000, 0xa45e00, 0x10c79600, 0xa45e00)]

def scan(raw, rs, label, lo, hi):
    end = raw + rs
    o = raw
    runs = []
    st = None
    ln = 0
    while o + 8 <= end:
        q = struct.unpack_from("<Q", data, o)[0]
        r = q - IB
        ok = lo <= r < hi
        if ok:
            if ln == 0:
                st = o
            ln += 1
        else:
            if ln >= 32:
                runs.append((ln, st))
            ln = 0
        o += 8
    if ln >= 32:
        runs.append((ln, st))
    print("=== %s runs pointing into [%#x,%#x):" % (label, lo, hi))
    for l, s in runs:
        print("   len=%-6d off=0x%X first=0x%X last=0x%X" % (
            l, s, struct.unpack_from("<Q", data, s)[0] - IB,
            struct.unpack_from("<Q", data, s + (l - 1) * 8)[0] - IB))

for n, va, vs, raw, rs in SECS:
    if n in (".rdata", ".data"):
        scan(raw, rs, n, 0x11200000, 0x11450000)
