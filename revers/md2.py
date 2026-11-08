import struct
p=r"C:\Program Files (x86)\Steam\steamapps\common\Rust\RustClient_Data\il2cpp_data\Metadata\global-metadata.dat"
d=open(p,'rb').read()
names=["stringLiteral","stringLiteralData","string","events","properties","methods","parameterDefaultValues","fieldDefaultValues","fieldAndParameterDefaultValueData","fieldMarshaledSizes","parameters","fields","genericParameters","genericParameterConstraints","genericContainers","nestedTypes","interfaces","vtableMethods","interfaceOffsets","typeDefinitions","images","assemblies","fieldRefs","referencedAssemblies","attributeData","attributeDataRange","unresolvedVirtualCallParameterTypes","unresolvedVirtualCallParameterRanges","windowsRuntimeTypeNames","windowsRuntimeStrings","exportedTypeDefinitions"]
hdr={}
for i,n in enumerate(names):
    off,size=struct.unpack_from('<II',d,8+i*8)
    hdr[n]=(off,size)
    print("%-38s off=0x%08X size=0x%X"%(n,off,size))

so,ss=hdr['string']
def getstr(idx):
    e=d.index(b'\0',so+idx)
    return d[so+idx:e].decode('utf-8','replace')
def findstr(s):
    i=d.find(s.encode(),so,so+ss)
    return i-so if i>=0 else -1

td_off,td_size=hdr['typeDefinitions']
fl_off,fl_size=hdr['fields']
print("typedeff at",hex(td_off),"size",hex(td_size),"fields",hex(fl_off),hex(fl_size))
for target in ["EntityRealm","ListHashSet`1","ListHashSet"]:
    ni=findstr(target)
    print("\n=== target",target,"nameIndex",ni,"===")
    if ni<0: continue
    found=[]
    for base,size in [(92,0x5C),(0x60,0x60),(0x58,0x58)]:
        for o in range(td_off,td_off+td_size-base,4):
            if struct.unpack_from('<i',d,o)[0]!=ni: continue
            vals=struct.unpack_from('<17i',d,o)
            fstart,mstart=vals[9],vals[10]
            counts=struct.unpack_from('<8H',d,o+68)
            fcount=counts[2]
            if 0<=fstart<200000 and 0<=fcount<200 and mstart<400000:
                found.append((base,o,vals,counts))
        if found: break
    print("candidates",len(found))
    for base,o,vals,counts in found[:4]:
        print(" -- at 0x%X structsize %d namespace='%s' parentIdx=%d fieldStart=%d fcount=%d mtok=%d"%(o,base,getstr(vals[1]) if vals[1]>=0 else '?',vals[5],vals[9],counts[2],vals[16]))
        for k in range(counts[2]):
            fo=fl_off+(vals[9]+k)*12
            fn,ft,tok=struct.unpack_from('<iiI',d,fo)
            print("      +? %-40s typeIndex=%d nameOff=%d"%(getstr(fn),ft,fn))
