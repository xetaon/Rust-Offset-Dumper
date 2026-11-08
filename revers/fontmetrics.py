import struct, sys

def read_tables(path):
    d = open(path, 'rb').read()
    num = struct.unpack('>H', d[4:6])[0]
    tabs = {}
    for i in range(num):
        off = 12 + i*16
        tag = d[off:off+4].decode('latin1')
        o, l = struct.unpack('>II', d[off+8:off+16])
        tabs[tag] = (o, l)
    return d, tabs

def parse(path):
    d, tabs = read_tables(path)
    head = tabs['head'][0]
    upem = struct.unpack('>H', d[head+18:head+20])[0]
    hhea = tabs['hhea'][0]
    asc, desc, gap = struct.unpack('>hhh', d[hhea+4:hhea+10])
    nhm = struct.unpack('>H', d[hhea+34:hhea+36])[0]
    hmtx = tabs['hmtx'][0]
    advances = [struct.unpack('>H', d[hmtx+i*4:hmtx+i*4+2])[0] for i in range(nhm)]

    # cmap format 4
    cmap_off = tabs['cmap'][0]
    n = struct.unpack('>H', d[cmap_off+2:cmap_off+4])[0]
    sub = None
    for i in range(n):
        pid, eid, off = struct.unpack('>HHI', d[cmap_off+4+i*8:cmap_off+12+i*8])
        fmt = struct.unpack('>H', d[cmap_off+off:cmap_off+off+2])[0]
        if fmt == 4 and (pid == 3 and eid == 1):
            sub = cmap_off+off
    if sub is None:
        return None
    segX2 = struct.unpack('>H', d[sub+6:sub+8])[0]
    seg = segX2//2
    endP = sub+14
    startP = endP+segX2+2
    deltaP = startP+segX2
    rangeP = deltaP+segX2
    gid = {}
    for s in range(seg):
        end = struct.unpack('>H', d[endP+s*2:endP+s*2+2])[0]
        start = struct.unpack('>H', d[startP+s*2:startP+s*2+2])[0]
        delta = struct.unpack('>h', d[deltaP+s*2:deltaP+s*2+2])[0]
        ro = struct.unpack('>H', d[rangeP+s*2:rangeP+s*2+2])[0]
        for c in range(start, min(end, 0xFFFF)+1):
            if ro == 0:
                g = (c + delta) & 0xFFFF
            else:
                addr = rangeP + s*2 + ro + (c-start)*2
                if addr+2 > len(d): continue
                g = struct.unpack('>H', d[addr:addr+2])[0]
                if g: g = (g + delta) & 0xFFFF
            if g: gid[c] = g
    return upem, asc, desc, gap, advances, gid

for path in sys.argv[1:]:
    m = parse(path)
    upem, asc, desc, gap, advances, gid = m
    print(path, 'upem', upem, 'asc', asc, 'desc', desc, 'gap', gap)
    widths = {}
    for c in range(32, 127):
        g = gid.get(c, 0)
        a = advances[g] if g < len(advances) else 0
        widths[c] = a
    px = lambda a: a*11.0/upem
    print('advances(units/px@11):')
    line = []
    for c, a in widths.items():
        line.append('%s=%d/%.3f' % (chr(c), a, px(a)))
    print(' '.join(line))
    uniq = sorted(set(widths.values()))
    print('unique units:', uniq, 'px:', ['%.3f' % px(u) for u in uniq])
