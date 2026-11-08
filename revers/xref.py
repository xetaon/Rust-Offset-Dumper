import struct, sys
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
text=[s for s in secs if s[0]=='.text'][0]
tname,tva,tvsz,tptr,trsz=text
target=int(sys.argv[1],0)
hits=[]
import re
# scan for E8 rel32 and E9
blob=data[tptr:tptr+trsz]
for i in range(len(blob)-5):
    if blob[i] in (0xE8,0xE9):
        rel=struct.unpack_from('<i',blob,i+1)[0]
        src=tva+i
        dst=src+5+rel
        if dst==target:
            hits.append((src,blob[i]))
for s,op in hits:
    print("%s at RVA %s (0x%X)"%('call' if op==0xE8 else 'jmp',hex(s),s))
print("total",len(hits))
