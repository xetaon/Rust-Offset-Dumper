import struct
P = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\RustClient_Data\il2cpp_data\Metadata\global-metadata.dat"
b=open(P,'rb').read()
o=0x2A049E0
print("dump 0x2A049E0..0x2A04E00")
for r in range(0,0x420,16):
    chunk=b[o+r:o+r+16]
    h=' '.join('%02X'%c for c in chunk)
    p=''.join(chr(c) if 32<=c<127 else '.' for c in chunk)
    print("0x%08X  %-47s  %s"%(o+r,h,p))
