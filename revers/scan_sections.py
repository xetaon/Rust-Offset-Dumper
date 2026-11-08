import sys
P = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\RustClient_Data\il2cpp_data\Metadata\global-metadata.dat"
d = open(P, "rb").read()
N = len(d)
CH = 0x4000
print("size", hex(N))
for off in range(0, N, CH):
    b = d[off:off+CH]
    printable = sum(1 for c in b if 32 <= c < 127 or c == 0)
    if printable / len(b) > 0.75:
        print("TEXT %#x .. %#x  ratio=%.2f" % (off, off+len(b), printable/len(b)))
