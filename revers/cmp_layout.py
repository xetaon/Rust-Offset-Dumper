import struct, sys
sys.path.insert(0, r"C:\Users\SystemX\Desktop\Rust-Offset-Dumper\tools")
import meta_rva as M
d = open(r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll", "rb").read(); IB = 0x180000000
md = M.Metadata(M.DEFAULT_METADATA)
SECS = [(0x1000,0x8e4400,0x400,0x8e4400),(0x8e6000,0xe2ce600,0x8e4800,0xe2ce600),
        (0xebb5000,0x20c6800,0xebb2e00,0x20c6800),(0x10c7c000,0xa45e00,0x10c79600,0xa45e00)]
def r2o(r):
    for va,vs,raw,rs in SECS:
        if va<=r<va+rs: return raw+(r-va)
TYPES=0xFBA9B30; SIZES=0x110EF100
def ptr(base,i):
    return r2o(struct.unpack_from("<Q",d,base+i*8)[0]-IB)
def tinfo(i):
    o=ptr(TYPES,i)
    if o is None: return None
    return struct.unpack_from("<Q",d,o)[0],(struct.unpack_from("<I",d,o+8)[0]>>16)&0xFF,struct.unpack_from("<I",d,o+8)[0]&0xFFFF
def sinfo(i):
    o=ptr(SIZES,i); return struct.unpack_from("<I",d,o)[0] if o else 0
PRIM={0x02:(1,1),0x03:(2,2),0x04:(1,1),0x05:(1,1),0x06:(2,2),0x07:(2,2),0x08:(4,4),
      0x09:(4,4),0x0A:(8,8),0x0B:(8,8),0x0C:(4,4),0x0D:(8,8),0x18:(8,8),0x19:(8,8)}
def resolve_def(ti):
    x=tinfo(ti)
    if not x: return None
    data,typ,attrs=x
    if typ==0x15:
        og=r2o(data-IB); tp=struct.unpack_from("<Q",d,og)[0]
        return resolve_def_ptr(tp)
    if typ in (0x11,0x12): return data
    return None
def resolve_def_ptr(tp):
    ot=r2o(tp-IB)
    data=struct.unpack_from("<Q",d,ot)[0]; typ=(struct.unpack_from("<I",d,ot+8)[0]>>16)&0xff
    if typ==0x15:
        og=r2o(data-IB); return resolve_def_ptr(struct.unpack_from("<Q",d,og)[0])
    if typ in (0x11,0x12): return data
    return None
def fsize(fi):
    x=tinfo(fi)
    if not x: return 8,8
    data,typ,attrs=x
    if typ in PRIM: return PRIM[typ]
    if typ==0x11:
        inst=sinfo(data); al=1
        while al*2<=min(inst,8) and inst%(al*2)==0: al*=2
        return inst,al
    return 8,8
def au(v,a): return (v+a-1)//a*a
def layout(tdi,cache):
    if tdi in cache: return cache[tdi]
    t=md.type(tdi); p=t["parent_type"]; cur=0
    if p>=0:
        pd=resolve_def(p)
        if pd is not None and pd<md.type_count: cur=layout(pd,cache)[0]
    off=md.sections["fields"][0]; fl=[]
    for k in range(t["field_count"]):
        b=off+(t["first_field"]+k)*12
        ni,fi,tok=struct.unpack_from("<iiI",md.data,b)
        x=tinfo(fi); attrs=x[2] if x else 0
        if attrs&0x10: continue
        sz,al=fsize(fi); cur=au(cur,al)
        fl.append((k,md.string(ni),cur,sz,tinfo(fi)[1],attrs))
        cur+=sz
    cache[tdi]=(cur,fl); return cache[tdi]

cache={}
ARRAYS={"Projectile":0xec2cb08,"AttackEntity":0xec4c4d0,"BasePlayer":0xEBF22B0}
for nm,arr in ARRAYS.items():
    tdi=[i for i in range(md.type_count) if md.type(i)["name"]==nm][0]
    size,fl=layout(tdi,cache)
    print("===",nm,"stored",hex(sinfo(tdi)),"pred",hex(size),"instance fields",len(fl))
    for j,(k,fn,off,sz,typ,attrs) in enumerate(fl[:80]):
        real=struct.unpack_from("<I",d,arr+j*4)[0]
        mark="" if real==off else ("POISON" if real==0x67676767 else "DIFF")
        if mark:
            print("  inst%3d ord%3d %-22s comp=0x%X real=0x%X sz=%d typ=%#x %s" % (j,k,fn[:22],off,real,sz,typ,mark))
