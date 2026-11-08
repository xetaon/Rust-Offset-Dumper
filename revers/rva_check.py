import struct, sys
sys.path.insert(0, r"C:\Users\SystemX\Desktop\Rust-Offset-Dumper\tools")
from reverse import Pe

DLL = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
BASE = 0x7FF8E0B20000

pe = Pe(DLL)
funcs = pe.functions()
begins = {f[0] for f in funcs}
print(f"image {len(pe.data):#x} bytes, functions {len(funcs)}")
print(f"sections: " + ", ".join(f"{s['name']}@{s['va']:#x}" for s in pe.sections))

targets = [
    ("PlayerWalkMovement::ClientInput", 0x7FF8E6D95EC0),
    ("BaseProjectile::DoAttack",        0x7FF8E2FFDD90),
    ("PerformanceUI::Update",           0x7FF8E8487650),
    ("DevControls::OnGUI",              0x7FF8E4E7B9A0),
    ("CursorManager::Update",           0x7FF8E64E0230),
    ("TOD_Sky::LateUpdate",             0x7FF8E1808550),
    ("ProjectileShoot::WriteToStream",  0x7FF8ED17A7D0),
    ("PlayerTickDelta",                 0x7FF8ECD93790),
    ("ProjectileAttack",                0x7FF8EBAF4600),
    ("BasePlayer::OnAttacked",          0x7FF8E180ADF0),
    ("Projectile::Update",              0x7FF8E6C26340),
    ("LootAllButton::OnClicked",        0x7FF8E515DB40),
    ("LootAllButton::Awake",            0x7FF8E515DDD0),
    ("icall SetPositionAndRotation",    0x7FF8F30E0360),
    ("icall Time::get_timeScale",       0x7FF8F30DF710),
    ("icall MoveGameObjectToScene",     0x7FF8F30E87D0),
]
for name, addr in targets:
    if addr < BASE:
        print(f"{name:34s} {addr:#x}  (heap/managed)")
        continue
    rva = addr - BASE
    f = pe.func_of(rva)
    mark = "FUNC-START" if rva in begins else ("in-func" if f else "NOT-IN-CODE")
    print(f"{name:34s} {addr:#x}  RVA={rva:#09x}  {mark}" + (f"  [{f[0]:#x}..{f[1]:#x}]" if f else ""))
