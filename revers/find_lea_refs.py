import struct
DLL = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
data = open(DLL, "rb").read()
IB = 0x180000000

# code sections
TEXT = (0x400, 0x8e4400)
IL2 = (0x8e4800, 0xe2ce600)

def va_off(o):
    # .text raw 0x400 va 0x1000 ; il2cpp raw 0x8e4800 va 0x8e6000
    if TEXT[0] <= o < TEXT[0] + TEXT[1]:
        return 0x1000 + (o - TEXT[0])
    if IL2[0] <= o < IL2[0] + IL2[1]:
        return 0x8e6000 + (o - IL2[0])
    return None

TARGET_LO, TARGET_HI = 0xEB0000, 0xEE0000  # region of field offset arrays

hits = []
for start, size in (TEXT, IL2):
    end = start + size
    i = start
    while i < end - 8:
        b0 = data[i]
        if b0 in (0x48, 0x4C) and data[i + 1] == 0x8D:
            modrm = data[i + 2]
            if (modrm & 0xC7) == 0x05:
                disp = struct.unpack_from("<i", data, i + 3)[0]
                target = (va_off(i) or 0) + 7 + disp
                if TARGET_LO <= target < TARGET_HI:
                    hits.append((i, va_off(i), target, data[i:i + 7].hex(), b0))
        i += 1

print("hits", len(hits))
for h in hits[:200]:
    print("off=0x%X va=0x%X -> 0x%X bytes=%s rex=%02x" % h)
