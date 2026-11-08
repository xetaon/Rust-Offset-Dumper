import struct, re, sys
sys.path.insert(0, r"C:\Users\SystemX\Desktop\Rust-Offset-Dumper\revers")
import rev_classes as rc
DLL=r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
data=open(DLL,'rb').read()
SENT=0x67676767
sections=[(".text",0x400,0x8e4400),("il2cpp",0x8e4800,0xe2ce600),
          (".rdata",0xebb2e00,0x20c6800),(".data",0x10c79600,0xa45e00)]

def locate(offsets):
    best=None
    for name,start,size in sections:
        end=min(start+size,len(data))
        for i in range(start, end-4, 4):
            if struct.unpack_from('<I',data,i)[0]!=offsets[0]:
                continue
            score=0
            for k,off in enumerate(offsets):
                p=i+4*k
                if p+4>end: break
                v=struct.unpack_from('<I',data,p)[0]
                if v==off: score+=1
                elif v==SENT: score+=1  # position plausible
            if best is None or score>best[0]:
                best=(score,hex(i),name)
    return best

for cls,rows in rc.EXPECTED.items():
    offs=[r[1] for r in rows]
    b=locate(offs)
    print(cls, "fields",len(offs),"best",b)
    if b:
        i=int(b[1],16)
        vals=[struct.unpack_from('<I',data,i+4*k)[0] for k in range(len(offs))]
        direct=sum(1 for k,v in enumerate(vals) if v==offs[k])
        sent=sum(1 for v in vals if v==SENT)
        print("   direct",direct,"sentinel",sent)
        # mismatches
        for k,(v,o) in enumerate(zip(vals,offs)):
            if v!=o and v!=SENT:
                print("   idx",k,"req",hex(o),"bin",hex(v))
