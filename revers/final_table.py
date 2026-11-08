import struct, sys
sys.path.insert(0, r"C:\Users\SystemX\Desktop\Rust-Offset-Dumper\tools")
from reverse import Pe

DLL = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
BASE = 0x7FF8E0B20000
pe = Pe(DLL)
d = pe.data
begins = {f[0] for f in pe.functions()}

def off2rva(off):
    for s in pe.sections:
        if s["raw"] <= off < s["raw"] + s["rawsize"]:
            return s["va"] + (off - s["raw"]), s["name"]
    return None, None

targets = [
    ("PerformanceUI::Update",   0x7967650),
    ("DevControls::OnGUI",      0x435b9a0),
    ("CursorManager::Update",   0x59c0230),
    ("LootAllButton::OnClicked",0x463DB40),
    ("LootAllButton::Awake",    0x463DDD0),
    ("PlayerWalkMovement::ClientInput", 0x6275EC0),
    ("BaseProjectile::DoAttack",0x24DDD90),
    ("TOD_Sky::LateUpdate",     0x0CE8550),
    ("Projectile::Update",      0x6106340),
]
for name, rva in targets:
    f = pe.func_of(rva)
    start = "START" if rva in begins else "mid"
    print("==", name)
    print("   abs  = %#x" % (BASE + rva))
    print("   rva  = %#x (%s)" % (rva, start))
    print("   func = %s" % (("%#x..%#x (%d bytes)" % (f[0], f[1], f[1]-f[0])) if f else "NOT IN .pdata"))
    pat = struct.pack("<Q", rva + 0x180000000)
    i = d.find(pat); slots=[]
    while i != -1 and len(slots) < 6:
        srva, sec = off2rva(i); slots.append("%#x (%s)" % (srva, sec)); i = d.find(pat, i+1)
    print("   methodptr-table slot = %s" % (", ".join(slots) if slots else "none"))
