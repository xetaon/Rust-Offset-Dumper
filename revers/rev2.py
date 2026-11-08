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

md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True

known = {
    'BaseProjectile_DoAttack': 0x24DDD90,
    'BaseProjectile_DidAttackClientside': 0x24CD110,
    'BaseProjectile_OnInput': 0x24E0920,
    'AttackEntity_StartAttackCooldown': 0x6851040,
    'AttackEntity_HasAttackCooldown': 0x68552B0,
    'AttackEntity_IsFullyDeployed': 0x6852A20,
}
def nearest(rva):
    best = '-' ; bd = 1 << 60
    for n, r in known.items():
        d = rva - r
        if 0 <= d < bd:
            bd = d; best = n + '+0x%X' % d
    return best

def scan(disps):
    for name, va, vsize, rawoff, rawsz in secs:
        if name not in ('il2cpp', 'text'):
            continue
        blob = data[rawoff:rawoff + rawsz]
        for disp in disps:
            pat = struct.pack('<I', disp)
            hits = []
            idx = 0
            while True:
                idx = blob.find(pat, idx)
                if idx < 0:
                    break
                # candidate instruction start within 8 bytes before disp
                found = None
                for back in range(4, 9):
                    s = idx - back
                    if s < 0:
                        continue
                    try:
                        ins = next(md.disasm(blob[s:s + 16], base + va + s))
                    except StopIteration:
                        continue
                    if ins.size != back + 4:
                        continue
                    if not ins.operands:
                        continue
                    mem = ins.operands[-1]
                    if mem.type != 3:  # X86_OP_MEM
                        continue
                    if mem.mem.disp != disp:
                        continue
                    if mem.mem.index != 0:
                        continue
                    if ins.mnemonic in ('movss', 'movups', 'movaps', 'mov', 'comiss', 'ucomiss', 'addss', 'subss', 'mulss', 'divss', 'movd', 'movq', 'cvtsi2ss', 'add', 'sub', 'and', 'or', 'xor', 'shr', 'shl', 'cmp'):
                        found = (ins)
                        break
                if found:
                    rva = va + idx - found.size + 4  # start rva
                    hits.append((rva, found.address - base, found))
                idx += 1
            if hits:
                print('\n### %s %s disp=0x%X hits=%d' % (name, 'sec', disp, len(hits)))
                for rva, _x, ins in hits[:30]:
                    print('  %08X  %-10s %-40s  near %s' % (ins.address - base, ins.mnemonic, ins.op_str, nearest(ins.address - base)))

scan([0x4A0, 0x4A4, 0x4A8, 0x49C, 0x498, 0x4B0, 0x460, 0x4C0, 0x4C4, 0x4F0, 0x348])
