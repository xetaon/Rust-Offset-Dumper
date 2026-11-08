import sys
sys.path.insert(0, r"C:\Users\SystemX\Desktop\Galaxy.Clinic Executor\scripts")
from galaxy.pe import PEImage
import collections, math

PATH = r"C:\Program Files\Roblox\Versions\version-9ac8595712b447a7\RobloxPlayerBeta.dll"
im = PEImage.from_path(PATH)
print(im)
print("base", hex(im.base), "entry", hex(im.entry_point))
for section in im.sections:
    data = im.section_data(section)
    counts = collections.Counter(data)
    entropy = -sum((count / len(data)) * math.log2(count / len(data)) for count in counts.values()) if data else 0
    print(f"{section.name:10s} va=0x{section.virtual_address:X} vs=0x{section.virtual_size:X} raw=0x{section.raw_size:X} ent={entropy:.3f} chars=0x{section.characteristics:X}")
print("exports", len(im.exports()))
for name, export in list(im.exports().items())[:40]:
    print(" ", name, hex(export.rva))
print("imports", len(im.imports()))
for item in im.imports()[:20]:
    print(" ", item.module, item.name, item.ordinal)
terms = [b"luau_load", b"luau_deserialize", b"lua_resume", b"lua_newthread", b"lua_pcall", b"lua_setidentity", b"Compiler::deserialize", b"Luau::", b"RSB1", b"cannot resume dead coroutine", b"WaitingHybridScriptsJob", b"luau_compile", b"luaL_"]
for term in terms:
    indices = []
    start = 0
    while True:
        idx = im.data.find(term, start)
        if idx < 0:
            break
        indices.append(idx)
        start = idx + 1
    print(term, len(indices), [hex(x) for x in indices[:10]], [hex(im.offset_to_va(x)) for x in indices[:5]])
