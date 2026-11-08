import struct
DLL = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
data = open(DLL, "rb").read()
SEC = {"rdata": (0xebb2e00, 0x20c6800), "data": (0x10c79600, 0xa45e00),
       "il2cpp": (0x8e4800, 0xe2ce600)}

def scan_qword(val, secname, limit=20):
    lo, sz = SEC[secname]
    pat = struct.pack("<Q", val)
    i = lo
    out = []
    while True:
        i = data.find(pat, i, lo + sz)
        if i == -1:
            break
        out.append(i)
        i += 1
        if len(out) > 200:
            break
    print("qword %#x in %s: %d hits" % (val, secname, len(out)))
    for o in out[:limit]:
        bits = struct.unpack_from("<I", data, o + 8)[0]
        print("   off=0x%X aligned16=%s data=%#x sp8=%#x bits=%#x typ16=%#x typ0=%#x next=%s" % (
            o, o % 16 == 0, struct.unpack_from("<Q", data, o)[0],
            struct.unpack_from("<Q", data, o + 8)[0], bits,
            (bits >> 16) & 0xff, bits & 0xff,
            data[o + 16:o + 24].hex()))
    return out

for v in (8570, 5604, 7227, 9199):
    scan_qword(v, "rdata", 6)
scan_qword(8570, "data", 6)
scan_qword(8570, "il2cpp", 6)
