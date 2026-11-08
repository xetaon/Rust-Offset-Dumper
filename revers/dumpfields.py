import sys, struct
sys.path.insert(0, r'C:\Users\SystemX\Desktop\Rust-Offset-Dumper\tools')
import meta_rva as M

MD = r'C:\Program Files (x86)\Steam\steamapps\common\Rust\RustClient_Data\il2cpp_data\Metadata\global-metadata.dat'
DLL = r'C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll'
meta = M.Metadata(MD)
pe = M.Pe(DLL)
mp = M.RvaMapper(meta, pe)

foff, fsize, fcount = meta.sections['fields']
print('field elem size', fsize / fcount, 'count', fcount)
F = int(fsize / fcount)

def fields(typename):
    t = None
    for i in range(meta.type_count):
        tt = meta.type(i)
        if tt['name'] == typename:
            t = tt
            break
    if not t:
        print(typename, 'not found'); return
    print('---', typename, 'fields', t['field_count'])
    for k in range(t['field_count']):
        b = foff + (t['first_field'] + k) * F
        name_idx, type_idx = struct.unpack_from('<ii', meta.data, b)
        tok = struct.unpack_from('<I', meta.data, b + 8)[0] if F >= 12 else 0
        print('  %-40s typeIdx=%d %s tok=%#x' % (meta.string(name_idx), type_idx, meta.string(meta.type(type_idx)['name']) if 0 <= type_idx < meta.type_count else '?', tok))

for n in ('LootAllButton', 'ItemIcon', 'LootPanel', 'PlayerLoot'):
    fields(n)

# find method at rva 0x1834db0
print('--- method at 0x1834db0')
import meta_rva
for img in meta.images():
    base = mp.table_base_for_image(img)
    if not base:
        continue
    for mi in range(img['method_start'] if 'method_start' in img else 0, 0):
        pass
# use method map: iterate all methods and compare rva (cached by image)
for i in range(meta.method_count):
    m = meta.method(i)
    r = mp.rva_for_method(i)
    if r == 0x1834db0:
        t = meta.type(m['declaring_type'])
        print('  idx', i, 'tok', hex(m['token']), 'class', t['name'], 'method', m['name'], 'flags', hex(m['flags']),
              'params', meta.method_params(m))
        break
else:
    print('  not found')
