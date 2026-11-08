import struct
P = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\RustClient_Data\il2cpp_data\Metadata\global-metadata.dat"
d = open(P, "rb").read()
print("file", hex(len(d)))
magic, ver = struct.unpack_from("<Ii", d, 0)
print("magic", hex(magic), "ver", ver)
names = """stringLiteral stringLiteralData string events properties methods parameterDefaultValues fieldDefaultValues fieldAndParameterDefaultValueData fieldMarshaledSizes parameters fields genericParameters genericParameterConstraints genericContainers nestedTypes interfaces vtableMethods interfaceOffsets typeDefinitions typeInlineArrays images assemblies fieldRefs referencedAssemblies attributeData attributeDataRange unresolvedVirtualCallParameterTypes unresolvedVirtualCallParameterRanges windowsRuntimeTypeNames windowsRuntimeStrings exportedTypeDefinitions""".split()
o = 8
for i, n in enumerate(names):
    off, size, count = struct.unpack_from("<iii", d, o)
    o += 12
    ok = 0 <= off <= len(d) and 0 <= size <= len(d) - off
    print("%-40s off=%#010x size=%#010x count=%-10d %s" % (n, off, size, count, "OK" if ok else "BAD"))
print("next int32 at header end:", struct.unpack_from("<i", d, o)[0])
