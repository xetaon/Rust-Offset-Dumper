import struct, sys
sys.path.insert(0, r"C:\Users\SystemX\Desktop\Rust-Offset-Dumper\tools")
from reverse import Pe

DLL = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
pe = Pe(DLL)
d = pe.data

def off2rva(off):
    for s in pe.sections:
        if s["raw"] <= off < s["raw"] + s["rawsize"]:
            return s["va"] + (off - s["raw"]), s["name"]
    return None, None

targets = [
    ("PerformanceUI::Update", 0x7967650),
    ("DevControls::OnGUI",    0x435b9a0),
    ("CursorManager::Update", 0x59c0230),
    ("TOD_Sky::LateUpdate",   0x0ce8550),
    ("Projectile::Update",    0x6106340),
    ("BaseProjectile::DoAttack", 0x24ddd90),
]
for name, rva in targets:
    print("==", name, hex(rva))
    f = pe.func_of(rva)
    print("   code: RVA", hex(rva), "func", (hex(f[0]), hex(f[1])) if f else None)
    pat = struct.pack("<Q", rva + 0x180000000)
    i = d.find(pat)
    n = 0
    while i != -1 and n < 10:
        srva, sec = off2rva(i)
        print("   ptr-table: file %#x -> RVA %#x (%s)" % (i, srva, sec))
        n += 1
        i = d.find(pat, i + 1)
    if n == 0:
        print("   ptr-table: none")
