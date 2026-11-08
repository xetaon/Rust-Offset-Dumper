import pefile, math, collections
p = r"C:\Program Files\Roblox\Versions\version-9ac8595712b447a7\RobloxPlayerBeta.exe"
pe = pefile.PE(p, fast_load=True)
d = open(p,'rb').read()
for s in pe.sections:
    b = d[s.PointerToRawData:s.PointerToRawData+s.SizeOfRawData]
    if not b:
        continue
    c = collections.Counter(b)
    ent = -sum((n/len(b))*math.log2(n/len(b)) for n in c.values())
    print(s.Name.decode(errors='replace').rstrip('\0'), len(b), round(ent,3), b[:32].hex(' '))
print("entry bytes:", d[pe.OPTIONAL_HEADER.AddressOfEntryPoint - pe.sections[0].VirtualAddress + pe.sections[0].PointerToRawData:][:64].hex(' '))
