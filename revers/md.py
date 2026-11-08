import struct, sys
p=r"C:\Program Files (x86)\Steam\steamapps\common\Rust\RustClient_Data\il2cpp_data\Metadata\global-metadata.dat"
d=open(p,'rb').read()
print("magic %08X version %d"%(struct.unpack_from('<I',d,0)[0],struct.unpack_from('<i',d,4)[0]))
names=["stringLiteralOffset","stringOffset","eventsOffset","propertiesOffset","methodsOffset","parameterDefaultValuesOffset","fieldDefaultValuesOffset","fieldAndParameterDefaultValueDataOffset","fieldMarshaledSizesOffset","parametersOffset","fieldsOffset","genericParametersOffset","genericParameterConstraintsOffset","genericContainersOffset","nestedTypesOffset","interfacesOffset","vtableMethodsOffset","interfaceOffsetsOffset","typeDefinitionsOffset","imagesOffset","assembliesOffset","fieldRefsOffset","referencedAssembliesOffset","attributeDataOffset","attributeDataRangeOffset","unresolvedVirtualCallParameterTypesOffset","unresolvedVirtualCallParameterRangesOffset","windowsRuntimeTypeNamesOffset","windowsRuntimeStringsOffset","exportedTypeDefinitionsOffset"]
# header is pairs offset,size
for i,n in enumerate(names):
    o=8+i*8
    if o+8>len(d): break
    off,size=struct.unpack_from('<II',d,o)
    print("%-45s off=0x%08X size=0x%X"%(n,off,size))
for s in [b"ListHashSet",b"EntityRealm",b"BaseNetworkable",b"clientEntities",b"entityList",b"%db947887b006e2498d1bff9fef4b4f822cedb3da"]:
    print(s, d.find(s))
