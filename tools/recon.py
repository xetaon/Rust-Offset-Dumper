"""Quick recon of GameAssembly.dll: PE layout, exports, metadata header."""
import sys, struct, os

PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
META = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\RustClient_Data\il2cpp_data\Metadata\global-metadata.dat"

def u16(b, o): return struct.unpack_from("<H", b, o)[0]
def u32(b, o): return struct.unpack_from("<I", b, o)[0]
def u64(b, o): return struct.unpack_from("<Q", b, o)[0]

with open(PATH, "rb") as f:
    data = f.read()

print("file size", len(data))
pe = u32(data, 0x3C)
print("e_lfanew", hex(pe), "sig", data[pe:pe+4])
machine = u16(data, pe+4)
nsec = u16(data, pe+6)
opt = pe+24
magic = u16(data, opt)
print("machine", hex(machine), "sections", nsec, "opt magic", hex(magic))
size_image = u32(data, opt+56)
print("SizeOfImage", hex(size_image))
ddoff = opt + (112 if magic == 0x20b else 96)
sec_table = opt + u16(data, pe+20)
secs = []
for i in range(nsec):
    o = sec_table + i*40
    name = data[o:o+8].rstrip(b"\0").decode("latin1")
    vsize, va, rawsize, rawptr = u32(data,o+8), u32(data,o+12), u32(data,o+16), u32(data,o+20)
    chars = u32(data,o+36)
    secs.append((name, va, vsize, rawptr, rawsize, chars))
    print(f"  {name:8s} va={va:#010x} vsize={vsize:#010x} raw={rawptr:#010x} rawsize={rawsize:#010x} chars={chars:#010x}")

def rva2off(rva):
    for name, va, vsize, rawptr, rawsize, chars in secs:
        if va <= rva < va + max(vsize, rawsize):
            return rawptr + (rva - va)
    return None

exp_rva, exp_size = u32(data, ddoff), u32(data, ddoff+4)
print("export dir rva", hex(exp_rva), "size", hex(exp_size))
if exp_rva:
    eo = rva2off(exp_rva)
    nfunc, nname = u32(data, eo+20), u32(data, eo+24)
    af, an, ao = u32(data, eo+28), u32(data, eo+32), u32(data, eo+36)
    print("exports funcs", nfunc, "names", nname)
    names = []
    for i in range(nname):
        no = rva2off(u32(data, rva2off(an)+i*4))
        end = data.index(b"\0", no)
        names.append(data[no:end].decode("latin1"))
    il2 = [n for n in names if n.startswith("il2cpp")]
    print("il2cpp exports:", len(il2))
    print("  ", ", ".join(il2[:40]))
    print("  first 10 export names:", names[:10])

print("metadata exists", os.path.exists(META))
with open(META, "rb") as f:
    m = f.read(256)
print("metadata size", os.path.getsize(META))
print("metadata header:", m[:32].hex())
print("sanity u32@0 =", hex(u32(m,0)))
