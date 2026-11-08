import struct
DLL = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
data = open(DLL, "rb").read()
IB = 0x180000000

def rva2off(rva):
    secs=[(".text",0x1000,0x8e4400,0x400,0x8e4400),("il2cpp",0x8e6000,0xe2ce600,0x8e4800,0xe2ce600),
          (".rdata",0xebb5000,0x20c6800,0xebb2e00,0x20c6800),(".data",0x10c7c000,0xa45e00,0x10c79600,0xa45e00),
          (".pdata",0x119b5000,0x82c800,0x116bf400,0x82c800)]
    for n,va,vs,raw,rs in secs:
        if va<=rva<va+rs: return raw+(rva-va)
    return None

bp_array_rva = 0xEBF22B0
needle = struct.pack('<Q', IB+bp_array_rva)
print("needle", needle.hex())
idx=0; hits=[]
while True:
    idx=data.find(needle, idx)
    if idx==-1: break
    hits.append(idx)
    idx+=1
print("qword hits:",[hex(h) for h in hits][:20], "count",len(hits))
# print surrounding qwords
for h in hits[:5]:
    print("--- around",hex(h))
    for k in range(-6,6):
        p=h+k*8
        if 0<=p and p+8<=len(data):
            v=struct.unpack_from('<Q',data,p)[0]
            print(k, hex(v))
