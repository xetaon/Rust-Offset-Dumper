import struct, sys
sys.path.insert(0, r"C:\Users\SystemX\Desktop\Rust-Offset-Dumper\tools")
import meta_rva as M
d = open(r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll","rb").read(); IB=0x180000000
md=M.Metadata(M.DEFAULT_METADATA)
SECS=[(0x1000,0x8e4400,0x400,0x8e4400),(0x8e6000,0xe2ce600,0x8e4800,0xe2ce600),(0xebb5000,0x20c6800,0xebb2e00,0x20c6800),(0x10c7c000,0xa45e00,0x10c79600,0xa45e00)]
def r2o(r):
    for va,vs,raw,rs in SECS:
        if va<=r<va+rs: return raw+(r-va)
TB=0xFBA9B30
def tinfo(i):
    o=r2o(struct.unpack_from("<Q",d,TB+i*8)[0]-IB)
    return struct.unpack_from("<Q",d,o)[0],(struct.unpack_from("<I",d,o+8)[0]>>16)&0xff,struct.unpack_from("<I",d,o+8)[0]&0xffff
def dump(nm, arr, n=None):
    tdi=[i for i in range(md.type_count) if md.type(i)["name"]==nm][0]
    t=md.type(tdi); fo=md.sections["fields"][0]
    print("===",nm,"tdi",tdi,"fields",t["field_count"])
    j=0
    for k in range(t["field_count"]):
        b=fo+(t["first_field"]+k)*12
        ni,fi,tok=struct.unpack_from("<iiI",md.data,b)
        data,typ,attrs=tinfo(fi)
        real=struct.unpack_from("<I",d,arr+j*4)[0] if j<200 else 0
        print(" ord%3d inst%3d %-26s ty=%#04x attrs=%#06x tok=%#x real=0x%X %s" % (
            k,j,md.string(ni)[:26],typ,attrs,tok,real,
            "POISON" if real==0x67676767 else ""))
        j+=1

dump("Projectile",0xec2cb08)
