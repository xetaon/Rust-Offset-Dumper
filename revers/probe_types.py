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

arr = 0xF0B0598
for i in list(range(12)) + [100,1000,5000,10000,25204]:
    q = struct.unpack_from("<Q", data, arr + i * 8)[0]
    r = q - IB
    o = r2o(r)
    if o is None:
        print(i, "unmap", hex(q)); continue
    q0 = struct.unpack_from("<Q", data, o)[0]
    bits = struct.unpack_from("<I", data, o + 8)[0]
    bits2 = struct.unpack_from("<I", data, o + 12)[0]
    print("idx=%5d rva=0x%X data=%#x bits=%#x type_lo=%#x type_hi=%#x rest=%#x sec=%s" % (
        i, r, q0, bits, bits & 0xFF, (bits >> 16) & 0xFF, bits2,
        ("rdata" if 0xebb2e00 <= o < 0xebb2e00+0x20c6800 else ("data" if 0x10c79600 <= o < 0x116bf400 else "?"))))
