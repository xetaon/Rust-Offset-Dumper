import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reverse as R
import capstone

pe = R.Pe(R.DLL)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
md.detail = True

REF = {'ClientEntitiesDecrypt': 0x1C3A336,
       'EntityListDecrypt': 0x1C5C780,
       'PlayerEyesDecrypt': 0x4030D30,
       'PlayerInventoryDecrypt': 0x3E204D0}

for name, (consts, wrapper, expected) in R.KNOWN.items():
    exp = [tuple(x) for x in expected]
    inv = R.invert_chain(exp)
    hits = []
    sets = [R.functions_with_const(pe, c) for c in consts]
    common = set.intersection(*sets) if sets else set()
    for f in sorted(common, key=lambda x: x[1] - x[0]):
        if f[1] - f[0] > 0x8000:
            continue
        code = pe.function_bytes(f)
        for b in R.extract_blocks(md, code, f[0]):
            ch = [tuple(x) for x in b['chain']]
            if ch == exp or (inv and ch == inv):
                hits.append((b['start'], 'direct' if ch == exp else 'inverse'))
    print(f"{name:28s} copies={len(hits)}")
    if name in REF:
        ref = REF[name]
        near = [h for h in hits if abs(h[0] - ref) < 0x300]
        print(f"    reference 0x{ref:X} matched={bool(near)}  {[(hex(a), d) for a, d in near]}")
        print(f"    copies: {[(hex(a), d) for a, d in hits[:10]]}")
