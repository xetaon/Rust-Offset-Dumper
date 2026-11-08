import sys
sys.path.insert(0, r"C:\Users\SystemX\Desktop\Galaxy.Clinic Executor\scripts")
from galaxy.pe import PEImage
import collections

PATH = r"C:\Program Files\Roblox\Versions\version-9ac8595712b447a7\RobloxPlayerBeta.exe"
im = PEImage.from_path(PATH)
ex = im.exports()
print("exports", len(ex))
for name, export in list(ex.items())[:120]:
    print(f"  {name} 0x{export.rva:X}")
imports = im.imports()
print("imports", len(imports))
print(collections.Counter(item.module for item in imports).most_common(30))

terms = [
    b"luau_load",
    b"luau_deserialize",
    b"lua_resume",
    b"lua_newthread",
    b"lua_pcall",
    b"lua_setidentity",
    b"Compiler::deserialize",
    b"Luau::",
    b"luaB_cocreate",
    b"luaB_coresume",
    b"luaB_pcall",
    b"cannot resume dead coroutine",
    b"RSB1",
    b"WaitingHybridScriptsJob",
]
for term in terms:
    indices = []
    start = 0
    while True:
        index = im.data.find(term, start)
        if index < 0:
            break
        indices.append(index)
        start = index + 1
    print(term, len(indices), [hex(x) for x in indices[:12]], [hex(im.offset_to_va(x)) for x in indices[:6]])
