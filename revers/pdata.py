import struct
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
def sec(n):
    for s in secs:
        if s[0]==n: return s
    return None
def rva2off(rva):
    for name,va,vsz,ptr,rsz in secs:
        if va<=rva<va+max(vsz,rsz): return ptr+(rva-va)
    return None
pd=sec('.pdata'); off=pd[3]; n=pd[4]//12
entries=[]
for i in range(n):
    b,e,u=struct.unpack_from('<III',data,off+i*12)
    entries.append((b,e,u))
entries.sort()
def find(rva):
    hit=[x for x in entries if x[0]<=rva<x[1]]
    return hit
import sys
for a in sys.argv[1:]:
    rva=int(a,0)
    print("RVA",hex(rva),"funcs",[(hex(x[0]),hex(x[1])) for x in find(rva)])
