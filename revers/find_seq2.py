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
        hits.append(i); i += 1
    print(label, [hex(x) for x in hits[:10]])
    for o in hits[:4]:
        print("   raw", hex(o), "next ints", [hex(struct.unpack_from("<i", d, o+4*k)[0]) for k in range(0,10)])

find_seq([0x6F8,0x710,0x718,0x728,0x748], "BP displayName..")
find_seq([0x6D0,0x6D8,0x6E0], "BP effects")
find_seq([0x358,0x368], "BP tick/team")
find_seq([0x2F0,0x318], "BP userid/blueprints")
find_seq([0x5E0,0x5E8], "BP inv/mounted")
find_seq([0x98,0xA0], "PM shoulders")
find_seq([0x3C0,0x3C4,0x3C8,0x3CC,0x3D0,0x3D4,0x3D8,0x3DC], "PM skin nums")
find_seq([0x670,0x678,0x6D8], "PM animator/modelstate")
