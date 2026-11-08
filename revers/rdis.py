import struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
data=open(PATH,'rb').read()
pe=struct.unpack_from('<I',data,0x3C)[0]
nsec=struct.unpack_from('<H',data,pe+6)[0]
optsz=struct.unpack_from('<H',data,pe+20)[0]
base=struct.unpack_from('<Q',data,pe+24+24)[0]
sec0=pe+24+optsz
secs=[]
for i in range(nsec):
    o=sec0+i*40
    name=data[o:o+8].rstrip(b'\0').decode('latin1')
    vsz,va,rsz,ptr=struct.unpack_from('<IIII',data,o+8)
    secs.append((name,va,vsz,ptr,rsz))
def rva2off(rva):
    for name,va,vsz,ptr,rsz in secs:
        if va<=rva<va+max(vsz,rsz): return ptr+(rva-va)
md=Cs(CS_ARCH_X86,CS_MODE_64)
start=int(sys.argv[1],0); end=int(sys.argv[2],0)
off=rva2off(start)
code=data[off:off+(end-start)]
for ins in md.disasm(code, base+start):
    print("%08X  %-26s %s %s"%(ins.address-base, ins.bytes.hex(), ins.mnemonic, ins.op_str))
