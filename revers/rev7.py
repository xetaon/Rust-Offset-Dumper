import struct
from capstone import *
PATH=r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
data=open(PATH,'rb').read(); pe=struct.unpack_from('<I',data,0x3C)[0]; nsec=struct.unpack_from('<H',data,pe+6)[0]; optsz=struct.unpack_from('<H',data,pe+20)[0]; optoff=pe+24
magic=struct.unpack_from('<H',data,optoff)[0]; base=struct.unpack_from('<Q',data,optoff+24)[0] if magic==0x20B else struct.unpack_from('<I',data,optoff+28)[0]
secs=[]; so=optoff+optsz
for i in range(nsec):
    o=so+i*40; name=data[o:o+8].split(b'\0')[0].decode(); vsize,va,rawsz,rawoff=struct.unpack_from('<IIII',data,o+8); secs.append((name,va,vsize,rawoff,rawsz))
def rva2off(rva):
    for n,va,vs,ro,rs in secs:
        if va<=rva<va+max(vs,rs): return ro+(rva-va)
md=Cs(CS_ARCH_X86,CS_MODE_64)
start=0x6EA2790; off=rva2off(start); code=data[off:off+0x140]
for ins in md.disasm(code,base+start):
    print('%08X %-9s %s'%(ins.address-base,ins.mnemonic,ins.op_str))
