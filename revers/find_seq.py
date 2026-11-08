import struct
d = open(r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll", "rb").read()
RD = (0xebb2e00, 0x20c6800)
def find_seq(vals, label):
    pat = b"".join(struct.pack("<i", v) for v in vals)
    hits = []
    i = RD[0]
    while True:
        i = d.find(pat, i, RD[0] + RD[1])
        if i == -1: break
        hits.append(i)
        i += 1
    print(label, "hits", [hex(x) for x in hits[:10]])
    for o in hits[:3]:
        rva = 0xebb5000 + (o - RD[0])
        print("  off", hex(o), "rva", hex(rva), "next:", [hex(struct.unpack_from("<i", d, o+4*k)[0]) for k in range(0, 12)])

find_seq([0x2F0,0x2F4,0x2F8,0x2FC,0x300,0x304,0x308,0x30C], "AttackEntity abs 2F0..")
find_seq([0x2F0,0x2F0+0x20], "BasePlayer 2F0 310?")
find_seq([0x98,0xA0,0xB8,0xD0,0xD4,0xE4,0xF4], "PlayerModel abs")
find_seq([0x28,0x34,0x38,0x3C,0x40,0x44,0x48,0x54], "Projectile abs")
