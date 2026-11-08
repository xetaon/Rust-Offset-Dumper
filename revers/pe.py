import struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
data = open(PATH,'rb').read()
pe = struct.unpack_from('<I', data, 0x3C)[0]
nsec = struct.unpack_from('<H', data, pe+6)[0]
optsz = struct.unpack_from('<H', data, pe+20)[0]
base = struct.unpack_from('<Q', data, pe+24+24)[0]
sec0 = pe+24+optsz
secs=[]
for i in range(nsec):
    o=sec0+i*40
    name=data[o:o+8].rstrip(b'\0').decode('latin1')
    vsz,va,rsz,ptr=struct.unpack_from('<IIII', data, o+8)
    secs.append((name,va,vsz,ptr,rsz))
print("imagebase",hex(base))
for s in secs: print(s[0],hex(s[1]),hex(s[2]),hex(s[3]),hex(s[4]))

def rva2off(rva):
    for name,va,vsz,ptr,rsz in secs:
        if va<=rva<va+max(vsz,rsz):
            return ptr+(rva-va)
    return None

md=Cs(CS_ARCH_X86,CS_MODE_64)
md.detail=False
for rva in [int(x,0) for x in sys.argv[1:]]:
    off=rva2off(rva)
    print("\n=== RVA",hex(rva),"off",hex(off) if off else None,"===")
    if off is None: continue
    code=data[off:off+0x220]
    for ins in md.disasm(code, base+rva):
        print("%08X  %-24s %s %s"%(ins.address-base, ins.bytes.hex(), ins.mnemonic, ins.op_str))
        if ins.mnemonic=='ret': break
