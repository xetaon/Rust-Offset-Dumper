import struct, sys
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

def secname(rva):
    for name, va, vsize, rawoff, rawsz in secs:
        if va <= rva < va + max(vsize, rawsz):
            return name
    return None

md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True

def disasm(rva, size, label):
    off = rva2off(rva)
    code = data[off:off+size]
    print('\n===== %s rva=0x%X =====' % (label, rva))
    n = 0
    for ins in md.disasm(code, base + rva):
        print('%08X  %-8s %s' % (ins.address - base, ins.mnemonic, ins.op_str))
        n += 1
        if n > 400:
            print('... truncated')
            break
    return

disasm(0x68552B0, 0x90, 'AttackEntity::HasAttackCooldown')
disasm(0x6851040, 0x90, 'AttackEntity::StartAttackCooldown')

# OnInput: disassemble until int3 padding run or 0x3000 bytes
rva = 0x24E0920
off = rva2off(rva)
code = data[off:off+0x6000]
print('\n===== BaseProjectile::OnInput rva=0x%X =====' % rva)
count = 0
for i, ins in enumerate(md.disasm(code, base + rva)):
    print('%08X  %-8s %s' % (ins.address - base, ins.mnemonic, ins.op_str))
    count += 1
    if count > 1200:
        print('... truncated')
        break
