import pefile, capstone, struct
PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
pe = pefile.PE(PATH, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
DATA = open(PATH,"rb").read()
print("sections:")
for s in pe.sections:
    print("  %-8s va=0x%08X vsz=0x%08X raw=0x%08X rsz=0x%08X flags=0x%08X" % (
        s.Name.rstrip(b'\x00').decode('latin1'), s.VirtualAddress, s.Misc_VirtualSize,
        s.PointerToRawData, s.SizeOfRawData, s.Characteristics))

def scan_calls(lo,hi,name):
    hits=[]
    for s in pe.sections:
        if not (s.Characteristics & 0x20000000):  # not executable
            continue
        va=s.VirtualAddress; vsz=s.Misc_VirtualSize; ro=s.PointerToRawData
        blob=DATA[ro:ro+vsz]
        for i in range(len(blob)-5):
            if blob[i]==0xE8:
                rel=struct.unpack_from("<i",blob,i+1)[0]
                tgt=va+i+5+rel
                if lo<=tgt<=hi:
                    hits.append((va+i,tgt))
    print("\n%s call sites: %d"%(name,len(hits)))
    for c,t in hits[:30]:
        print("   call at 0x%X -> 0x%X"%(c,t))
    return hits

# include function starts in a wider window
ce = scan_calls(0x1C3A300,0x1C3A340,"client_entities getter")
el = scan_calls(0x1C5C780,0x1C5C780,"entity_list getter exact")
# also scan for the address as a qword pointer (methodPointers / vtables)
def scan_ptr(val,name):
    b=struct.pack("<Q",IB+val)
    hits=[]
    st=0
    while True:
        i=DATA.find(b,st)
        if i<0: break
        hits.append(i); st=i+1
    print("\n%s pointer (0x%X) occurrences: %d"%(name,IB+val,len(hits)))
    for i in hits[:30]:
        print("   file off 0x%X"%i)
    return hits

scan_ptr(0x1C5C780,"entity_list fn")
scan_ptr(0x1C3A320,"client_entities fn(mid)")
