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
o, l = tables["name"]
fmt, count, str_off = struct.unpack(">HHH", d[o:o+6])
names = {}
for i in range(count):
    b = o + 6 + i * 12
    pid, eid, lid, nid, ln, off = struct.unpack(">HHHHHH", d[b:b+12])
    raw = d[o + str_off + off:o + str_off + off + ln]
    try:
        txt = raw.decode("utf-16-be") if pid in (0, 3) else raw.decode("latin-1")
    except Exception:
        continue
    if nid in (1, 2, 4, 6, 16, 17) and nid not in names:
        names[nid] = (pid, txt)
for k, v in sorted(names.items()):
    print(k, v)
print("UAL tags:", [t for t in tables if t.startswith("U")])
