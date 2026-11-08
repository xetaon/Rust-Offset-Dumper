import struct, sys, json

P = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\RustClient_Data\il2cpp_data\Metadata\global-metadata.dat"
d = open(P, "rb").read()

SEC = {}
o = 8
names = """stringLiteral stringLiteralData string events properties methods parameterDefaultValues fieldDefaultValues fieldAndParameterDefaultValueData fieldMarshaledSizes parameters fields genericParameters genericParameterConstraints genericContainers nestedTypes interfaces vtableMethods interfaceOffsets typeDefinitions typeInlineArrays images assemblies fieldRefs referencedAssemblies attributeData attributeDataRange unresolvedVirtualCallParameterTypes unresolvedVirtualCallParameterRanges windowsRuntimeTypeNames windowsRuntimeStrings exportedTypeDefinitions""".split()
for n in names:
    off, size, count = struct.unpack_from("<iii", d, o); o += 12
    SEC[n] = (off, size, count)

S_OFF, S_SIZE, NSTR = SEC["string"]
def st(i):
    if i < 0 or i >= S_SIZE: return None
    e = d.find(b"\0", S_OFF + i)
    if e < 0: return None
    try: return d[S_OFF + i:e].decode("utf-8")
    except: return d[S_OFF + i:e].decode("latin1")

T_OFF, T_SIZE, NT = SEC["typeDefinitions"]
M_OFF, M_SIZE, NM = SEC["methods"]
print("type size", T_SIZE / NT, "method size", M_SIZE / NM)

def read_type(i):
    b = T_OFF + i * 82
    nameIdx, nsIdx = struct.unpack_from("<ii", d, b)
    byval, decl, parent = struct.unpack_from("<iii", d, b + 8)
    gen = struct.unpack_from("<H", d, b + 20)[0]
    flags = struct.unpack_from("<I", d, b + 22)[0]
    firstField, firstMethod, firstEvent, firstProp = struct.unpack_from("<iiii", d, b + 26)
    nested, ifaces, vtable, ifaceOff = struct.unpack_from("<iiii", d, b + 42)
    mc, pc, fc, ec, ntc, vc, ic, ioc = struct.unpack_from("<8H", d, b + 58)
    bitfield, token = struct.unpack_from("<II", d, b + 74)
    return dict(idx=i, name=st(nameIdx), ns=st(nsIdx), nameIdx=nameIdx, nsIdx=nsIdx,
                byval=byval, decl=decl, parent=parent, gen=gen, flags=flags,
                firstMethod=firstMethod, methodCount=mc, firstField=firstField, fieldCount=fc,
                token=token, bitfield=bitfield)

def read_method(i):
    b = M_OFF + i * 32
    nameIdx = struct.unpack_from("<i", d, b)[0]
    decl = struct.unpack_from("<H", d, b + 4)[0]
    ret = struct.unpack_from("<i", d, b + 6)[0]
    paramStart = struct.unpack_from("<i", d, b + 14)[0]
    gen = struct.unpack_from("<H", d, b + 18)[0]
    token = struct.unpack_from("<I", d, b + 20)[0]
    flags, iflags, slot, pcnt = struct.unpack_from("<4H", d, b + 24)
    return dict(idx=i, name=st(nameIdx), nameIdx=nameIdx, decl=decl, ret=ret,
                paramStart=paramStart, gen=gen, token=token, flags=flags,
                iflags=iflags, slot=slot, paramCount=pcnt)

if __name__ == "__main__":
    targets = sys.argv[1:] or ["ItemIcon", "LootAllButton", "PerformanceUI", "DevControls", "CursorManager", "PlayerWalkMovement", "BaseProjectile", "TOD_Sky", "Projectile"]
    for i in range(NT):
        t = read_type(i)
        if t["name"] in targets or (t["name"] and any(t["name"].startswith(x) for x in targets)):
            print("TYPE %5d %s.%s token=%#x firstMethod=%d count=%d flags=%#x" % (i, t["ns"], t["name"], t["token"], t["firstMethod"], t["methodCount"], t["flags"]))
            for mi in range(t["firstMethod"], t["firstMethod"] + t["methodCount"]):
                m = read_method(mi)
                print("   %6d %-40s token=%#x slot=%d params=%d flags=%#x" % (mi, m["name"], m["token"], m["slot"], m["paramCount"], m["flags"]))
