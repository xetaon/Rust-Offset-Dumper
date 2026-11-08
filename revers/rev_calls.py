import pefile, capstone, struct

PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
pe = pefile.PE(PATH, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
with open(PATH, "rb") as f:
    DATA = f.read()

def off(rva): return pe.get_offset_from_rva(rva)

def dis(rva, count=80, label="", start_at=None):
    o = off(rva)
    code = DATA[o:o+count*10]
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True
    print("\n===== %s RVA 0x%X =====" % (label, rva))
    n=0
    for ins in md.disasm(code, IB+rva):
        print("0x%X  %-22s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
        n+=1
        if n>=count: break
    print("===== end =====")

# 1. prologue before the known decryptor body
dis(0x1C3A2C0, 70, "around client_entities (prologue)")
dis(0x1C5C740, 70, "around entity_list (prologue)")

# 2. scan .text for direct calls/jmps to the two functions (any target in a window)
text = pe.sections[0]
text_rva = text.VirtualAddress
text_sz = text.Misc_VirtualSize
text_off = text.PointerToRawData
blob = DATA[text_off:text_off+text_sz]

targets = {}
for name, lo, hi in [("client_entities", 0x1C3A2C0, 0x1C3A340),
                     ("entity_list", 0x1C5C740, 0x1C5C790)]:
    hits=[]
    for i in range(len(blob)-5):
        if blob[i] == 0xE8:
            rel = struct.unpack_from("<i", blob, i+1)[0]
            tgt = text_rva + i + 5 + rel
            if lo <= tgt <= hi:
                hits.append((text_rva+i, tgt))
    targets[name]=hits
    print("\n%s call sites:" % name)
    for c,t in hits[:40]:
        print("  call at RVA 0x%X -> 0x%X" % (c,t))
    print("  total", len(hits))

# 3. For the first few callers, show some context after the call
for name in targets:
    for c,t in targets[name][:6]:
        dis(c, 45, "%s caller @0x%X" % (name, c))
