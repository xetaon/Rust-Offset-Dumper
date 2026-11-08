import pefile, capstone, struct
PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
pe = pefile.PE(PATH, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
DATA = open(PATH,"rb").read()

def find_pat(pat):
    hits=[]
    for s in pe.sections:
        if not (s.Characteristics & 0x20000000): continue
        va=s.VirtualAddress; vsz=s.Misc_VirtualSize; ro=s.PointerToRawData
        blob=DATA[ro:ro+vsz]
        st=0
        while True:
            i=blob.find(pat,st)
            if i<0: break
            hits.append(va+i); st=i+1
    return hits

for name,pat in [("0x606A395C",bytes.fromhex("5C396A60")),
                 ("0x380CDD1C",bytes.fromhex("1CDD0C38")),
                 ("0x49F666DD",bytes.fromhex("DD66F649")),
                 ("0x165993A",bytes.fromhex("3A996501")),
                 ("0x6EA51C6",bytes.fromhex("C651EA06"))]:
    h=find_pat(pat)
    print("\n%s occurrences: %d"%(name,len(h)))
    for x in h[:25]: print("   0x%X"%x)

# Find which functions contain 0x606A395C and whether they also contain 0x380CDD1C
h1=set(find_pat(bytes.fromhex("5C396A60")))
h2=set(find_pat(bytes.fromhex("1CDD0C38")))
# cluster nearby addresses (within 0x400)
def cluster(pts):
    pts=sorted(pts); out=[]
    for p in pts:
        if out and p-out[-1][-1] < 0x400: out[-1].append(p)
        else: out.append([p])
    return out
print("\nclusters containing BOTH list constants:")
for c in cluster(h1):
    if any(abs(a-b)<0x400 for a in c for b in h2):
        print("   cluster:", [hex(x) for x in c])
