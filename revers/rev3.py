import struct
from capstone import *
PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
data = open(PATH, 'rb').read()
pe = struct.unpack_from('<I', data, 0x3C)[0]
nsec = struct.unpack_from('<H', data, pe + 6)[0]
optsz = struct.unpack_from('<H', data, pe + 20)[0]
optoff = pe + 24
magic = struct.unpack_from('<H', data, optoff)[0]
base = struct.unpack_from('<Q', data, optoff + 24)[0] if magic == 0x20B else struct.unpack_from('<I', data, optoff + 28)[0]
secs = []
so = optoff + optsz
for i in range(nsec):
    o = so + i * 40
    name = data[o:o+8].split(b'\0')[0].decode()
    vsize, va, rawsz, rawoff = struct.unpack_from('<IIII', data, o + 8)
    secs.append((name, va, vsize, rawoff, rawsz))
def rva2off(rva):
    for name, va, vsize, rawoff, rawsz in secs:
        if va <= rva < va + max(vsize, rawsz):
            return rawoff + (rva - va)
    return None
md = Cs(CS_ARCH_X86, CS_MODE_64)
for label, rva, ln in [('BaseProjectile::DoAttack', 0x24DDD90, 0x1200), ('BaseProjectile::DidAttackClientside', 0x24CD110, 0x1200)]:
    off = rva2off(rva); code = data[off:off+ln]
    print('\n===== %s =====' % label)
    cnt = 0
    for ins in md.disasm(code, base + rva):
        s = '%08X  %-9s %s' % (ins.address - base, ins.mnemonic, ins.op_str)
        print(s)
        cnt += 1
        if cnt > 900: break
