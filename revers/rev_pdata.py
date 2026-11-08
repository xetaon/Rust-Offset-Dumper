import pefile, capstone, struct
PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
pe = pefile.PE(PATH, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
DATA = open(PATH,"rb").read()

# parse .pdata
pd = [s for s in pe.sections if s.Name.rstrip(b'\0')==b'.pdata'][0]
blob = DATA[pd.PointerToRawData:pd.PointerToRawData+pd.Misc_VirtualSize]
funcs=[]
for i in range(0,len(blob)-12,12):
    beg,end,unw = struct.unpack_from("<III",blob,i)
    if beg==0 and end==0: continue
    if beg < pd.VirtualAddress and beg < 0x1000: continue
    funcs.append((beg,end))
# pdata BeginAddress is an RVA in the image
print("total pdata funcs", len(funcs))
lo,hi=0x1C5A000,0x1C5D500
sel=[(b,e) for b,e in funcs if lo<=b<=hi and e>b]
sel.sort()
print("functions in 0x%X..0x%X: %d"%(lo,hi,len(sel)))
for b,e in sel:
    print("  0x%X..0x%X size=0x%X"%(b,e,e-b))
