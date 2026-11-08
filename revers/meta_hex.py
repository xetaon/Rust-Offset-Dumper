import struct
P = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\RustClient_Data\il2cpp_data\Metadata\global-metadata.dat"
b=open(P,'rb').read()
def hx(o,n,label):
    print("\n--- %s @0x%X ---"%(label,o))
    for r in range(0,n,16):
        chunk=b[o+r:o+r+16]
        h=' '.join('%02X'%c for c in chunk)
        p=''.join(chr(c) if 32<=c<127 else '.' for c in chunk)
        print("0x%08X  %-47s  %s"%(o+r,h,p))
hx(0x17C,64,"stringLiteralOffset 0x17C")
hx(0xF346,64,"stringLiteralData 0xF346")
hx(0x2787CD,96,"stringOffset 0x2787CD")
hx(0x2A04A00,96,"BaseNetworkable area")
# interpret stringLiteral entries
print("\nstringLiteral entries:")
for i in range(6):
    o=0x17C+i*8
    ln,di=struct.unpack_from("<ii",b,o)
    print("  [%d] len=%d dataIdx=0x%X"%(i,ln,di))
