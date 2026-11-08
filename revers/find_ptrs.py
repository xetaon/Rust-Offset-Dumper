import pefile, struct
PATH = r"C:\Program Files\Roblox\Versions\version-9ac8595712b447a7\RobloxPlayerBeta.exe"
pe = pefile.PE(PATH, fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
data = open(PATH,'rb').read()

def va_to_file_off(va):
    rva = va - base
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (rva - s.VirtualAddress)
    return None

def file_off_to_va(off):
    for s in pe.sections:
        if s.PointerToRawData <= off < s.PointerToRawData + s.SizeOfRawData:
            return base + s.VirtualAddress + (off - s.PointerToRawData)
    return None

strings = {}
for a in [b"RSB1", b"cannot resume dead coroutine", b"cannot resume non-suspended coroutine", b"Lua function expected", b"Lua function", b"expected"]:
    i = data.find(a)
    print(a, hex(file_off_to_va(i)) if i>=0 else 'not found')
    if i>=0: strings[a] = file_off_to_va(i)

for a,va in strings.items():
    print("\n", a, "VA", hex(va))
    for label, needle in [("va64", struct.pack('<Q', va)), ("rva32", struct.pack('<I', va-base))]:
        start=0; hits=[]
        while True:
            j=data.find(needle,start)
            if j<0: break
            hits.append(j); start=j+1
        print(label, len(hits), [hex(file_off_to_va(x)) for x in hits[:20]])

# Search for "Lua function expected" in chunks? maybe split strings
for a in [b"Lua function", b"function expected", b"cocreate", b"create", b"coroutine"]:
    hits=[]; start=0
    while len(hits)<10:
        j=data.find(a,start)
        if j<0: break
        hits.append(hex(file_off_to_va(j))); start=j+1
    print(a, hits)
