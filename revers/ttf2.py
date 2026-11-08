import struct
p = r"C:\Users\SystemX\Desktop\SteamAccGen\lanapixel-regular.ttf"
d = open(p, "rb").read()
num = struct.unpack(">H", d[4:6])[0]
tables = {}
for i in range(num):
    off = 12 + i * 16
    tag = d[off:off+4].decode("latin-1")
    o, l = struct.unpack(">II", d[off+8:off+16])
    tables[tag] = (o, l)
o, l = tables["post"]
print("isFixedPitch:", struct.unpack(">I", d[o+12:o+16])[0])
o, l = tables["OS/2"]
panose = d[o+32:o+42]
print("panose:", list(panose))
o, l = tables["head"]
units = struct.unpack(">H", d[o+18:o+20])[0]
print("unitsPerEm:", units)
o, l = tables["hhea"]
asc, desc, gap = struct.unpack(">hhh", d[o+4:o+10])
print("asc/desc/gap:", asc, desc, gap)
