import sys, struct
sys.path.insert(0, r'C:\Users\SystemX\Desktop\Rust-Offset-Dumper\tools')
import meta_rva as M

MD = r'C:\Program Files (x86)\Steam\steamapps\common\Rust\RustClient_Data\il2cpp_data\Metadata\global-metadata.dat'
meta = M.Metadata(MD)
foff, fsize, fcount = meta.sections['fields']
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
        print('  %-44s typeIdx=%d' % (meta.string(name_idx), type_idx))

for n in ('PlayerInventory', 'PlayerLoot', 'ItemIcon', 'LootGrid', 'InventoryGrid'):
    fields(n)
