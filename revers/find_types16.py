import struct
DLL=r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
data=open(DLL,'rb').read()
for name,raw,rs in [(".rdata",0xebb2e00,0x20c6800),("il2cpp",0x8e4800,0xe2ce600),(".data",0x10c79600,0xa45e00)]:
    end=raw+rs; best=(0,None); run=0; start=None; o=raw
    while o+16<=end:
        typ=data[o+8]
        ok = 1<=typ<=0x21 and (data[o+9]==0 or data[o+9] in (0,1,2,4,8,0x10))
        if ok:
            if run==0: start=o
            run+=1
        else:
            if run>best[0]:best=(run,start)
            run=0
        o+=16
    if run>best[0]:best=(run,start)
    print(name,"longest 16-byte type-like run:",best[0],hex(best[1]) if best[1] else None)
