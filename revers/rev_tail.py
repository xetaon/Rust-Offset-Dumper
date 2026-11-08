import pefile, capstone
P=r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
pe=pefile.PE(P,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase; D=open(P,'rb').read()
o=pe.get_offset_from_rva(0x41EACC0)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64); md.detail=True
for ins in md.disasm(D[o:o+0x1B0], IB+0x41EACC0):
    print("0x%X %-20s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
