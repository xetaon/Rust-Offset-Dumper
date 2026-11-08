import pefile, capstone, struct
PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
pe = pefile.PE(PATH, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
DATA = open(PATH,"rb").read()
def va2off(va): return pe.get_offset_from_rva(va)
def dis(va,count=110,label=""):
    o=va2off(va); code=DATA[o:o+count*10]
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64); md.detail=True
    print("\n===== %s @0x%X ====="%(label,va))
    n=0
    for ins in md.disasm(code,IB+va):
        print("0x%X  %-22s %s %s"%(ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str))
        n+=1
        if n>=count: break
    print("===== end =====")

for h in [0x1C3B275,0x1C406DF,0x1C4986F,0x21B20F5,0x1C3A32F]:
    dis(h-16, 95, "inlined clientEntities")
