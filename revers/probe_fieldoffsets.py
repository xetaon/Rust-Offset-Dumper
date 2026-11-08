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

arr = 0x110EF100
for i in (0, 1, 2, 500, 5604, 7227, 8570, 9199, 32117):
    q = struct.unpack_from("<Q", data, arr + i * 8)[0]
    r = q - IB
    o = r2o(r)
    if o is None:
        print(i, "-> unmap", hex(q)); continue
    ints = struct.unpack_from("<8i", data, o)
    print("idx=%5d rva=0x%X bytes=%s ints=%s" % (i, r, data[o:o+32].hex(), [hex(x) if x >= 0 else x for x in ints]))
