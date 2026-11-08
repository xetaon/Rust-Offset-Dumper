import struct, os, sys

META = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\RustClient_Data\il2cpp_data\Metadata\global-metadata.dat"
with open(META, "rb") as f:
    m = f.read()

u32 = lambda o: struct.unpack_from("<I", m, o)[0]
i32 = lambda o: struct.unpack_from("<i", m, o)[0]

print("size", len(m), "sanity", hex(u32(0)), "version", i32(4))

# v39 header: sanity, version, then 35-ish (offset,size,offset,size...) pairs
p = 8
pairs = []
while p + 8 <= 8 + 8 * 60:
    off, size = u32(p), u32(p + 4)
    if off == 0 and size == 0:
        pairs.append((off, size)); p += 8; continue
    if off > len(m) or size > len(m) or off + size > len(m):
        break
    pairs.append((off, size)); p += 8

names = ["stringLiteral","stringLiteralData","string","events","properties","methods",
         "paramDefault","fieldDefault","fieldDefaultData","fieldMarshaledSizes","parameters",
         "fields","genericParameters","genericParamConstraints","genericContainers","nestedTypes",
         "interfaces","vtableMethods","interfaceOffsets","typeDefinitions","images","assemblies",
         "fieldRefs","referencedAssemblies","attributeData","attributeDataRange",
         "unresolvedVirtualCallParamTypes","unresolvedVirtualCallParamRanges",
         "windowsRuntimeTypeNames","windowsRuntimeStrings","exportedTypeDefinitions",
         "??","??","??","??"]
for i, (off, size) in enumerate(pairs):
    nm = names[i] if i < len(names) else "?"
    print(f"  [{i:2d}] {nm:32s} off={off:#010x} size={size:#010x} ({size})")

# sanity checks
def pair(i): return pairs[i]
soff, ssize = pair(2)
print("\nstring section first 200 bytes:", m[soff:soff+200])
td_off, td_size = pair(19)
print("typeDefinitions: off", hex(td_off), "size", hex(td_size), "count@0x5c?", td_size / 0x5C)
f_off, f_size = pair(11)
print("fields: off", hex(f_off), "size", hex(f_size), "count@0x14?", f_size / 0x14)
m_off, m_size = pair(5)
print("methods: off", hex(m_off), "size", hex(m_size), "count@0x2c?", m_size / 0x2C)
