import pefile, capstone, sys

PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
pe = pefile.PE(PATH, fast_load=True)
image_base = pe.OPTIONAL_HEADER.ImageBase
print("ImageBase = 0x%X" % image_base)
print("TimeDateStamp = 0x%X" % pe.FILE_HEADER.TimeDateStamp)
print("SizeOfImage = 0x%X" % pe.OPTIONAL_HEADER.SizeOfImage)

def rva_to_off(rva):
    return pe.get_offset_from_rva(rva)

def disasm(rva, count=160, label=""):
    off = rva_to_off(rva)
    with open(PATH, "rb") as f:
        f.seek(off)
        code = f.read(count * 8)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True
    print("\n===== %s RVA 0x%X (file 0x%X) =====" % (label, rva, off))
    n = 0
    for ins in md.disasm(code, image_base + rva):
        print("0x%X  %-24s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
        n += 1
        if n >= count:
            break
    print("===== end =====")

for rva, name, cnt in [
    (0x1C3A336, "client_entities_decryption", 200),
    (0x1C5C780, "entity_list_decryption", 200),
    (0x88C4A0, "il2cpp_gchandle_get_target", 60),
]:
    try:
        disasm(rva, cnt, name)
    except Exception as e:
        print("ERR", name, e)
