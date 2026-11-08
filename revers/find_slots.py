import sys, struct
sys.path.insert(0, r"C:\Users\SystemX\Desktop\Rust-Offset-Dumper\tools")
from reverse import Pe

DLL = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
pe = Pe(DLL)
d = open(DLL, "rb").read()
print("len", hex(len(d)))
def rva2off(r):
    for s in pe.sections:
        if s["va"] <= r < s["va"] + s["rawsize"]:
            return s["raw"] + (r - s["va"])
    return None
def off2rva(o):
    for s in pe.sections:
        if s["raw"] <= o < s["raw"] + s["rawsize"]:
            return s["va"] + (o - s["raw"])
    return None

known = {
    "PerformanceUI::Update": 0x7967650,
    "LootAllButton::OnClicked": 0x463DB40,
    "LootAllButton::Awake": 0x463DDD0,
    "DevControls::OnGUI": 0x435B9A0,
    "CursorManager::Update": 0x59C0230,
    "PlayerWalkMovement::ClientInput": 0x6275EC0,
    "BaseProjectile::DoAttack": 0x24DDD90,
    "TOD_Sky::LateUpdate": 0xCE8550,
    "Projectile::Update": 0x6106340,
}
IMAGE_BASE = 0x180000000
for name, rva in known.items():
    pat = struct.pack("<Q", IMAGE_BASE + rva)
    hits = []
    start = 0
    while True:
        i = d.find(pat, start)
        if i < 0: break
        hits.append(i)
        start = i + 1
        if len(hits) > 20: break
    print("%-34s RVA %#x hits=%d -> slots %s" % (name, rva, len(hits), [hex(off2rva(h)) for h in hits[:6]]))
