"""
Rust-Offset-Dumper static probe: LootAllButton::OnClicked / instant-loot path.
Reads GameAssembly.dll from the local Rust install, prints PE facts and
disassembles the region around the known RVA 0x463DB40.

Usage: py -3 tools/rev_loot.py
"""
import os
import struct
import sys

import capstone

GAME = r"C:\Program Files (x86)\Steam\steamapps\common\Rust"
DLL = os.path.join(GAME, "GameAssembly.dll")

U16 = lambda b, o: struct.unpack_from("<H", b, o)[0]
U32 = lambda b, o: struct.unpack_from("<I", b, o)[0]


class Pe:
    def __init__(self, path):
        with open(path, "rb") as f:
            self.data = f.read()
        d = self.data
        pe = U32(d, 0x3C)
        self.pe = pe
        self.nsec = U16(d, pe + 6)
        opt = pe + 24
        magic = U16(d, opt)
        self.image_base = struct.unpack_from("<Q", d, opt + 24)[0]
        self.size_of_image = U32(d, opt + 56)
        dd = opt + (112 if magic == 0x20B else 96)
        self.dir = [struct.unpack_from("<II", d, dd + i * 8) for i in range(16)]
        st = opt + U16(d, pe + 20)
        self.sections = []
        for i in range(self.nsec):
            o = st + i * 40
            self.sections.append(dict(
                name=d[o:o + 8].rstrip(b"\0").decode("latin1"),
                vsize=U32(d, o + 8), va=U32(d, o + 12),
                rawsize=U32(d, o + 16), raw=U32(d, o + 20),
                chars=U32(d, o + 36)))

    def rva2off(self, rva):
        for s in self.sections:
            if s["va"] <= rva < s["va"] + max(s["vsize"], s["rawsize"]):
                return s["raw"] + (rva - s["va"])
        return None

    def read(self, rva, n):
        o = self.rva2off(rva)
        return self.data[o:o + n] if o is not None else b""

    def functions(self):
        rva, size = self.dir[3]  # exception directory (.pdata)
        out = []
        if not rva or not size:
            return out
        o = self.rva2off(rva)
        for i in range(size // 12):
            b, e, u = struct.unpack_from("<III", self.data, o + i * 12)
            out.append((b, e))
        out.sort()
        return out


def main():
    pe = Pe(DLL)
    print("GameAssembly:", DLL, os.path.getsize(DLL), "bytes")
    print("ImageBase 0x%X  SizeOfImage 0x%X  sections %d" % (pe.image_base, pe.size_of_image, pe.nsec))
    for s in pe.sections:
        print("  %-8s va=0x%08X vsize=0x%08X raw=0x%08X chars=0x%08X" %
              (s["name"], s["va"], s["vsize"], s["raw"], s["chars"]))

    rva = 0x463DB40
    funcs = pe.functions()
    print("\nFunctions in .pdata:", len(funcs))
    match = [f for f in funcs if f[0] <= rva < f[1]]
    print("RVA 0x%X inside %s" % (rva, ("0x%X..0x%X (len 0x%X)" % (match[0][0], match[0][1], match[0][1]-match[0][0])) if match else "NOTHING"))

    start = (match[0][0] if match else rva) - 0x40
    end = (match[0][1] if match else rva + 0x200) + 0x20
    code = pe.read(start, end - start)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True
    print("\n--- disasm 0x%X..0x%X ---" % (start, end))
    for ins in md.disasm(code, start):
        mark = "  <== target" if ins.address == rva else ""
        print("0x%08X  %-24s %s %s%s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str, mark))


if __name__ == "__main__":
    main()
