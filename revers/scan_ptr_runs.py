import struct, sys
DLL = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\GameAssembly.dll"
data = open(DLL, "rb").read()

secs = [(".text", 0x1000, 0x8e4400, 0x400, 0x8e4400),
        ("il2cpp", 0x8e6000, 0xe2ce600, 0x8e4800, 0xe2ce600),
        (".rdata", 0xebb5000, 0x20c6800, 0xebb2e00, 0x20c6800),
        (".data", 0x10c7c000, 0xa45e00, 0x10c79600, 0xa45e00),
        (".pdata", 0x119b5000, 0x82c800, 0x116bf400, 0x82c800)]

def sec_of_off(o):
    for n, va, vs, raw, rs in secs:
        if raw <= o < raw + rs:
            return n
    return None

def sec_of_rva(r):
    for n, va, vs, raw, rs in secs:
        if va <= r < va + rs:
            return n
    return None

def scan(name, raw, rs, minrun=500):
    end = raw + rs
    o = raw
    runs = []
    run_start = None
    run_len = 0
    kind = {}
    while o + 8 <= end:
        q = struct.unpack_from("<Q", data, o)[0]
        ok = False
        sn = None
        if 0x180000000 <= q < 0x180000000 + 0x12000000:
            r = q - 0x180000000
            sn = sec_of_rva(r)
            if sn in (".rdata", ".data", "il2cpp", ".text"):
                ok = True
        if ok:
            if run_len == 0:
                run_start = o
            run_len += 1
            kind[sn] = kind.get(sn, 0) + 1
        else:
            if run_len >= minrun:
                runs.append((run_len, run_start, dict(kind)))
            run_len = 0
            kind = {}
        o += 8
    if run_len >= minrun:
        runs.append((run_len, run_start, dict(kind)))
    print("===", name, "runs>=", minrun)
    for ln, st, kd in runs:
        print("  len=%-6d off=0x%X rva=0x%X -> %s" % (
            ln, st, (0xebb5000 + (st - 0xebb2e00)) if name == ".rdata" else
            (0x10c7c000 + (st - 0x10c79600)), kd))

for n, va, vs, raw, rs in secs:
    if n in (".data", ".rdata"):
        scan(n, raw, rs)
