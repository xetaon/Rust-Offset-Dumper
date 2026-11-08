import sys
sys.path.insert(0, r"C:\Users\SystemX\AppData\Local\Temp\opencode")
import meta_parse as M

want = [
    (24641, "Update", "PerformanceUI::Update", 0x110ADD78),
    (6156, "OnClicked", "LootAllButton::OnClicked", 0x10F88868),
    (6156, "Awake", "LootAllButton::Awake", 0x10F88878),
    (5862, "OnGUI", "DevControls::OnGUI", 0x10F79360),
    (7896, "Update", "CursorManager::Update", 0x10FE48F0),
    (8664, "ClientInput", "PlayerWalkMovement::ClientInput", 0x1100D138),
    (3452, "DoAttack", "BaseProjectile::DoAttack", 0x10EED5C8),
    (12823, "LateUpdate", "TOD_Sky::LateUpdate", 0x10D02E30),
    (8570, "Update", "Projectile::Update", 0x11006E10),
]
for tid, mname, label, slot in want:
    t = M.read_type(tid)
    found = []
    for mi in range(t["firstMethod"], t["firstMethod"] + t["methodCount"]):
        m = M.read_method(mi)
        if m["name"] == mname:
            found.append((mi, m))
    print(label, "type", tid, t["name"], "count", t["methodCount"], "slot", hex(slot))
    for mi, m in found:
        idx_by_tok = m["token"] & 0xFFFFFF
        print("   idx=%d token=%#x (tokidx=%d=%#x) slot-hdr=%#x  slot-tok*8=%#x" % (mi, m["token"], idx_by_tok, idx_by_tok, slot - idx_by_tok*8, slot - idx_by_tok*8))
