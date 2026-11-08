import mmap, struct, re, sys

P = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\RustClient_Data\il2cpp_data\Metadata\global-metadata.dat"
with open(P,"rb") as f:
    b = f.read()

def find_all(needle):
    out=[]
    st=0
    while True:
        i=b.find(needle, st)
        if i<0: break
        out.append(i); st=i+1
    return out

for s in [b"BaseNetworkable", b"ClientEntities", b"clientEntities", b"entityList", b"EntityRealm", b"%db947887b006e2498d1bff9fef4b4f822cedb3da"]:
    locs = find_all(s)
    print("\n=== %s : %d hits ===" % (s.decode('ascii','replace'), len(locs)))
    for i in locs[:12]:
        a=max(0,i-48); z=min(len(b),i+len(s)+48)
        chunk=b[a:z]
        # printable preview with dots
        pv=''.join(chr(c) if 32<=c<127 else '.' for c in chunk)
        print("  off 0x%X : %s" % (i, pv))
