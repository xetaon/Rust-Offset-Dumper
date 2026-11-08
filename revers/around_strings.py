import pefile, re
p = r"C:\Program Files\Roblox\Versions\version-9ac8595712b447a7\RobloxPlayerBeta.exe"
pe = pefile.PE(p, fast_load=True)
d = open(p,'rb').read()
def off(va):
    rva=va-pe.OPTIONAL_HEADER.ImageBase
    for s in pe.sections:
        if s.VirtualAddress<=rva<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData):
            return s.PointerToRawData+rva-s.VirtualAddress
for va in [0x146713564,0x147283750,0x147283728,0x1473e9c96]:
    o=off(va)
    chunk=d[o-192:o+320]
    print("\n==== ",hex(va)," ====")
    print(repr(chunk))
    print(chunk.hex(' '))
