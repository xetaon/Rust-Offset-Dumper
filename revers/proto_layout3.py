import struct, sys
sys.path.insert(0, r"C:\Users\SystemX\Desktop\Rust-Offset-Dumper\tools")
import meta_rva as M
DLL = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
d = open(DLL, "rb").read(); IB = 0x180000000
md = M.Metadata(M.DEFAULT_METADATA)
SECS = [(0x1000,0x8e4400,0x400,0x8e4400),(0x8e6000,0xe2ce600,0x8e4800,0xe2ce600),
        (0xebb5000,0x20c6800,0xebb2e00,0x20c6800),(0x10c7c000,0xa45e00,0x10c79600,0xa45e00)]
def r2o(r):
    for va,vs,raw,rs in SECS:
        if va<=r<va+rs: return raw+(r-va)
TYPES=0xFBA9B30; SIZES=0x110EF100
def ptr(base,i):
    o=r2o(struct.unpack_from("<Q",d,base+i*8)[0]-IB); return o
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
    if typ==0x15:  # genericinst -> Il2CppGenericClass*
        og=r2o(data-IB)
        if og is None: return None
        tp=struct.unpack_from("<Q",d,og)[0]
        return resolve_def_ptr(tp)
    if typ in (0x11,0x12): return data
    return None
def resolve_def_ptr(tp):
    ot=r2o(tp-IB)
    if ot is None: return None
    data=struct.unpack_from("<Q",d,ot)[0]; bits=struct.unpack_from("<I",d,ot+8)[0]; typ=(bits>>16)&0xff
    if typ==0x15:
        og=r2o(data-IB)
        tp2=struct.unpack_from("<Q",d,og)[0]
        return resolve_def_ptr(tp2)
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
    if tdi<0 or tdi>=md.type_count: return (0,[])
    t=md.type(tdi)
    p=t["parent_type"]; cur=0
    if p>=0:
        pd=resolve_def(p)
        if pd is not None and pd<md.type_count:
            cur=layout(pd,cache)[0]
        elif pd is None:
            # parent external -> use sizes? unknown
            cur=0
    off=md.sections["fields"][0]; fl=[]
    for k in range(t["field_count"]):
        b=off+(t["first_field"]+k)*12
        ni,fi,tok=struct.unpack_from("<iiI",md.data,b)
        x=tinfo(fi); attrs=x[2] if x else 0
        if attrs&0x10: continue
        sz,al=fsize(fi); cur=au(cur,al)
        fl.append((k,md.string(ni),cur,sz,tinfo(fi)[1]))
        cur+=sz
    cache[tdi]=(cur,fl); return cache[tdi]
cache={}
names=("BasePlayer","Projectile","AttackEntity","PlayerModel")
tdis={}
for i in range(md.type_count):
    n=md.type(i)["name"]
    if n in names: tdis[n]=i
for n in names:
    tdi=tdis[n]
    p=md.type(tdi)["parent_type"]; pd=resolve_def(p)
    print(n,"tdi",tdi,"parent_idx",p,"parent_def",pd, md.type(pd)["name"] if pd and pd<md.type_count else "?", "stored",hex(sinfo(tdi)),"pred",hex(layout(tdi,cache)[0]))
    print("   last fields:", layout(tdi,cache)[1][-3:])
