import struct
from capstone import *
PATH=r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
data=open(PATH,'rb').read(); pe=struct.unpack_from('<I',data,0x3C)[0]; nsec=struct.unpack_from('<H',data,pe+6)[0]; optsz=struct.unpack_from('<H',data,pe+20)[0]; optoff=pe+24
magic=struct.unpack_from('<H',data,optoff)[0]; base=struct.unpack_from('<Q',data,optoff+24)[0] if magic==0x20B else struct.unpack_from('<I',data,optoff+28)[0]
secs=[]; so=optoff+optsz
for i in range(nsec):
    o=so+i*40; name=data[o:o+8].split(b'\0')[0].decode(); vsize,va,rawsz,rawoff=struct.unpack_from('<IIII',data,o+8); secs.append((name,va,vsize,rawoff,rawsz))
md=Cs(CS_ARCH_X86,CS_MODE_64)
for name,va,vs,ro,rs in secs:
    if name!='il2cpp': continue
    blob=data[ro:ro+rs]
    pat=struct.pack('<I',0x460)
    idx=0; hits=0
    while True:
        idx=blob.find(pat,idx)
        if idx<0: break
        # try instruction starts 2..8 bytes before disp
        for back in range(2,9):
            s=idx-back
            if s<0: continue
            try: ins=next(md.disasm(blob[s:s+16], base+va+s))
            except StopIteration: continue
            if ins.size!=back+4: continue
            if not ins.operands: continue
            mem=ins.operands[-1]
            if mem.type!=3 or mem.mem.disp!=0x460 or mem.mem.index!=0: continue
            if ins.mnemonic in ('mov','movss','movsd','movups','movaps') and ins.operands[0].type==3:
                print('%08X %-9s %s'%(ins.address-base,ins.mnemonic,ins.op_str))
                hits+=1
            break
        idx+=1
        if hits>200: break
