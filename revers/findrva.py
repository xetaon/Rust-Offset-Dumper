import sys
sys.path.insert(0, r'C:\Users\SystemX\Desktop\Rust-Offset-Dumper\tools')
import meta_rva as M

MD = r'C:\Program Files (x86)\Steam\steamapps\common\Rust\RustClient_Data\il2cpp_data\Metadata\global-metadata.dat'
DLL = r'C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll'
meta = M.Metadata(MD)
pe = M.Pe(DLL)
mp = M.RvaMapper(meta, pe)

targets = {0x7e0e0, 0xa43e050, 0x869fa0, 0x833030, 0x1834db0, 0x31d20, 0x8253f0}
found = {}
want = ('Assembly-CSharp.dll', 'Assembly-CSharp-firstpass.dll', 'Facepunch.Unity.dll')
for im in meta.images:
    if im['name'] not in want:
        continue
    print(im['name'], 'types', im['first_type'], im['type_count'])
    for ti in range(im['first_type'], im['first_type'] + im['type_count']):
        t = meta.type(ti)
        for mi in range(t['first_method'], t['first_method'] + t['method_count']):
            m = meta.method(mi)
            info = mp.rva_for_method(m)
            r = info["rva"] if info else None
            if r in targets:
                found[r] = (mi, m, t)
                print('  %#x -> class=%s method=%s tok=%#x flags=%#x params=%s' % (
                    r, t['name'], m['name'], m['token'], m['flags'], meta.method_params(m)))
print('missing:', [hex(x) for x in targets if x not in found])
