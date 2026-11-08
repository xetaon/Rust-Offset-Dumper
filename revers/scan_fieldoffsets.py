import struct, sys, os
DLL = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
data = open(DLL, "rb").read()

# anchors (declared-order index -> expected offset) from the request
anchors = [(3,0x2F0),(8,0x318),(16,0x358),(24,0x398),(29,0x3B8),(31,0x3C8),
           (56,0x440),(74,0x4C0),(84,0x508),(90,0x530),(93,0x548),(94,0x550),
           (113,0x5E0),(114,0x5E8),(157,0x710),(158,0x718),(164,0x748)]

def scan(name, start, size):
    end = min(start+size, len(data))
    region = data[start:end]
    hits=0
    # fast scan for the first anchor value at index 3
    needle = struct.pack('<I', 0x2F0)
    idx = region.find(needle)
    while idx != -1:
        if idx % 4 == 0 and idx >= 3*4:
            base = idx - 3*4
            ok=True
            for (i,off) in anchors:
                p=base+i*4
                if p+4>len(region): ok=False;break
                if struct.unpack_from('<I',region,p)[0]!=off: ok=False;break
            if ok:
                hits+=1
                print(f"MATCH {name} raw=0x{start+base:X} file=0x{start+base:X}")
            idx = region.find(needle, idx+1)
        else:
            idx = region.find(needle, idx+1)
    print(f"{name}: hits={hits}")

secs = [
 ("il2cpp",0x8e4800,0xe2ce600),
 (".rdata",0xebb2e00,0x20c6800),
 (".data",0x10c79600,0xa45e00),
]
for n,s,z in secs: scan(n,s,z)
