import pefile, capstone
PATH=r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
pe=pefile.PE(PATH,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
DATA=open(PATH,"rb").read()
def va2off(va): return pe.get_offset_from_rva(va)
def dis(va,size,label):
    o=va2off(va); code=DATA[o:o+size]
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64); md.detail=True
    print("\n===== %s 0x%X..0x%X ====="%(label,va,va+size))
    for ins in md.disasm(code,IB+va):
        print("0x%X  %-20s %s %s"%(ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str))
    print("===== end =====")
for va,sz,name in [(0x1C5A240,0xC2,"f1"),(0x1C5A310,0x4A,"f2"),(0x1C5A960,0x28,"f3"),
                   (0x1C5A9B0,0x28,"f4"),(0x1C5A9F0,0x28,"f5"),(0x1C5AA40,0x21,"f6"),
                   (0x1C5AA80,0x28,"f7"),(0x1C5AC50,0x6F,"f8"),(0x1C5B660,0x35,"f9"),
                   (0x1C5B6A0,0x59,"f10"),(0x1C5B700,0x71,"f11"),(0x1C5B780,0x59,"f12")]:
    dis(va,sz,name)
