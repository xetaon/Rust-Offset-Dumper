import sys, struct
sys.path.insert(0, r"C:\Users\SystemX\Desktop\Rust-Offset-Dumper\tools")
import meta_rva as M
d = open(M.DEFAULT_DLL, "rb").read()
pe = M.Pe(M.DEFAULT_DLL)
IB = M.IMAGE_BASE
md = M.Metadata(M.DEFAULT_METADATA)

def r2o(r):
    return pe.rva_to_off(r)
def q(rva):
    return struct.unpack_from("<Q", d, r2o(rva))[0]

# find candidate Il2CppType table: pointer at index 43666 -> struct with data=5604, type=0x12
def is_type_def_ptr(val, tdi, typ=0x12):
    o = r2o(val - IB)
    if o is None: return False
    data = struct.unpack_from("<Q", d, o)[0]
    bits = struct.unpack_from("<I", d, o + 8)[0]
    return data == tdi and ((bits >> 16) & 0xFF) == typ

# scan for qword == ptr to a type struct with data 5604
target_o = None
# find any Il2CppType structs with data 5604 by scanning .data/.rdata for qword 5604 followed by bits type 0x12
cands = []
for secname in (".rdata", ".data"):
    s = next(x for x in pe.sections if x["name"] == secname)
    start, end = s["raw"], s["raw"] + s["rawsize"]
    pat = struct.pack("<Q", 5604)
    i = start
    while True:
        i = d.find(pat, i, end)
        if i == -1: break
        if i + 12 <= end:
            bits = struct.unpack_from("<I", d, i + 8)[0]
            if ((bits >> 16) & 0xFF) == 0x12:
                rva = s["va"] + (i - s["raw"])
                cands.append(rva)
        i += 8
print("BasePlayer Il2CppType struct candidates:", [hex(x) for x in cands[:20]])

def find_table_for(struct_rva, index, label):
    pat = struct.pack("<Q", IB + struct_rva)
    hits = []
    for secname in (".rdata", ".data", ".text", "il2cpp"):
        s = next((x for x in pe.sections if x["name"] == secname), None)
        if not s: continue
        start, end = s["raw"], s["raw"] + s["rawsize"]
        i = start
        while True:
            i = d.find(pat, i, end)
            if i == -1: break
            pos = i - index * 8
            if pos >= 0:
                rva = s["va"] + (pos - s["raw"]) if start <= pos < end else None
                if rva is not None:
                    hits.append(rva)
            i += 1
    print(label, "candidate table bases for index", index, ":", [hex(x) for x in hits[:20]])
    return hits

for sr in cands[:5]:
    find_table_for(sr, 43666, "type-table")
