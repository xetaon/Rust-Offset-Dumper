import pefile, capstone, struct, sys, os

PATH = r"C:\Program Files\Roblox\Versions\version-9ac8595712b447a7\RobloxPlayerBeta.exe"
pe = pefile.PE(PATH, fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
print("ImageBase", hex(base), "SizeOfImage", hex(pe.OPTIONAL_HEADER.SizeOfImage), "Entry", hex(base + pe.OPTIONAL_HEADER.AddressOfEntryPoint))
for s in pe.sections:
    print(s.Name.decode(errors='replace').rstrip('\0'), hex(base+s.VirtualAddress), hex(s.Misc_VirtualSize), hex(s.PointerToRawData), hex(s.SizeOfRawData), hex(s.Characteristics))

data = open(PATH, 'rb').read()

def file_off_to_va(off):
    for s in pe.sections:
        if s.PointerToRawData <= off < s.PointerToRawData + s.SizeOfRawData:
            return base + s.VirtualAddress + (off - s.PointerToRawData)
    return None

def va_to_file_off(va):
    rva = va - base
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (rva - s.VirtualAddress)
    return None

anchors = [b"RSB1", b"cannot resume dead coroutine", b"cannot resume non-suspended coroutine", b"Lua function expected"]
for a in anchors:
    print("\nANCHOR", a)
    start = 0
    count = 0
    while True:
        i = data.find(a, start)
        if i < 0 or count >= 8:
            break
        va = file_off_to_va(i)
        print("file", hex(i), "va", hex(va) if va else None)
        start = i+1
        count += 1

# find rip-relative refs to a target VA by scanning .text for opcodes 48/4C 8D/8B with modrm 05/0D/15/1D/25/2D/35/3D
text = None
for s in pe.sections:
    if s.Name.startswith(b'.text'):
        text = s
        break

def xrefs_to(target_va, limit=100):
    out = []
    buf = data[text.PointerToRawData:text.PointerToRawData+text.SizeOfRawData]
    tstart = base + text.VirtualAddress
    for i in range(len(buf)-7):
        if buf[i] not in (0x48, 0x4C):
            continue
        if buf[i+1] not in (0x8D, 0x8B, 0x89):
            continue
        modrm = buf[i+2]
        if (modrm & 0xC7) != 0x05:
            continue
        disp = struct.unpack_from('<i', buf, i+3)[0]
        addr = tstart + i + 7 + disp
        if addr == target_va:
            out.append(tstart+i)
            if len(out) >= limit:
                break
    return out

for a in anchors:
    i = data.find(a)
    if i < 0: continue
    va = file_off_to_va(i)
    print("\nXREFS to", a, hex(va))
    for x in xrefs_to(va):
        off = va_to_file_off(x)
        prev = data[max(0,off-24):off]
        print("  ", hex(x), "prev:", prev.hex(' '))
