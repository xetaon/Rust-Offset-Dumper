import struct
DLL=r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
data=open(DLL,'rb').read()
IB=0x180000000
# section map
secs=[(".text",0x1000,0x8e4400,0x400,0x8e4400),("il2cpp",0x8e6000,0xe2ce600,0x8e4800,0xe2ce600),
      (".rdata",0xebb5000,0x20c6800,0xebb2e00,0x20c6800),(".data",0x10c7c000,0xa45e00,0x10c79600,0xa45e00),
      (".pdata",0x119b5000,0x82c800,0x116bf400,0x82c800)]
def rva2off(r):
    for n,va,vs,raw,rs in secs:
        if va<=r<va+rs: return raw+(r-va)
    return None
def off2rva(o):
    for n,va,vs,raw,rs in secs:
        if raw<=o<raw+rs: return va+(o-raw)
    return None

def plausible(t_rva):
    o=rva2off(t_rva)
    if o is None or o+16>len(data): return False
    bits=struct.unpack_from('<I',data,o+8)[0]
    typ=(bits>>16)&0xFF if False else (bits & 0xff)
    return 2<= (bits & 0xff) <= 0x21

# scan .rdata and .data for runs of qwords pointing to plausible Il2CppType
for name,va,vs,raw,rs in [(".rdata",0xebb5000,0x20c6800,0xebb2e00,0x20c6800),(".data",0x10c7c000,0xa45e00,0x10c79600,0xa45e00)]:
    best=(0,None)
    o=raw; end=raw+rs
    run=0; runstart=None
    while o+8<=end:
        q=struct.unpack_from('<Q',data,o)[0]
        ok=False
        if IB<=q<IB+0x13000000:
            ok=plausible(q-IB)
        if ok:
            if run==0: runstart=o
            run+=1
        else:
            if run>best[0]: best=(run,runstart)
            run=0
        o+=8
    if run>best[0]: best=(run,runstart)
    print(name,"longest plausible qword run:",best[0],hex(best[1]) if best[1] else None)
