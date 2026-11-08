import sys, struct, time
sys.path.insert(0, r"C:\Users\SystemX\Desktop\Galaxy.Clinic Executor\scripts")
from galaxy.winmem import open_process, ProcessMemoryError, enable_debug_privilege
from galaxy.pe import PEImage
from galaxy.luau_finder import find_rip_xrefs, _scan_rip_xrefs_in_bytes, find_function_start

PATH = r"C:\Program Files\Roblox\Versions\version-9ac8595712b447a7\RobloxPlayerBeta.exe"
im = PEImage.from_path(PATH)
pid = 10264

def read_image(process, module):
    image = bytearray(module.size)
    missing = 0
    for region in process.module_regions(module):
        delta = region.base - module.base
        if delta < 0 or delta >= module.size:
            continue
        amount = min(region.size, module.size - delta)
        # Try whole region, then 64 KiB chunks, then 4 KiB pages.
        chunks = [(region.base, amount)]
        for chunk_base, chunk_size in chunks:
            try:
                data = process.read(chunk_base, chunk_size)
                image[chunk_base - module.base:chunk_base - module.base + len(data)] = data
                continue
            except ProcessMemoryError:
                pass
            cursor = 0
            while cursor < chunk_size:
                size = min(0x10000, chunk_size - cursor)
                try:
                    data = process.read(chunk_base + cursor, size)
                    start = chunk_base + cursor - module.base
                    image[start:start + len(data)] = data
                except ProcessMemoryError:
                    # try pages
                    page = 0
                    while page < size:
                        psize = min(0x1000, size - page)
                        try:
                            data = process.read(chunk_base + cursor + page, psize)
                            start = chunk_base + cursor + page - module.base
                            image[start:start + len(data)] = data
                        except ProcessMemoryError:
                            missing += psize
                        page += psize
                cursor += size
    return bytes(image), missing

with open_process(pid) as process:
    module = process.module("RobloxPlayerBeta.exe")
    print("module", module)
    image, missing = read_image(process, module)
    print("read image", len(image), "missing", missing, "nonzero", sum(1 for b in image if b))
    base = module.base

    def va(rva):
        return base + rva

    def off(address):
        return address - base

    def print_xrefs(text):
        rva = im.data.find(text)
        if rva < 0:
            print("string not on disk", text)
            return
        target = base + (im.offset_to_va(rva) - im.base)
        print(f"\nstring {text!r} rva=0x{target-base:X} va=0x{target:X}")
        xrefs = list(_scan_rip_xrefs_in_bytes(image, base, target))
        print("rip xrefs", [(hex(x.address), hex(x.address-base)) for x in xrefs][:20])
        needle = struct.pack("<Q", target)
        pointers = []
        start = 0
        while True:
            i = image.find(needle, start)
            if i < 0:
                break
            pointers.append(base + i)
            start = i + 1
        print("qword pointers", [(hex(p), hex(p-base)) for p in pointers][:20])
        for pointer in pointers[:10]:
            second = list(_scan_rip_xrefs_in_bytes(image, base, pointer))
            print("  refs to pointer", hex(pointer), [(hex(x.address), hex(x.address-base)) for x in second][:10])
        return target, xrefs

    cursor = print_xrefs(b"RSB1")
    print_xrefs(b"cannot resume dead coroutine")
    print_xrefs(b"cannot resume non-suspended coroutine")
    print_xrefs(b"error in error handling")
    print_xrefs(b"Lua function")

    try:
        import capstone
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
        md.detail = True
    except Exception as exc:
        print("capstone unavailable", exc)
        md = None

    def disasm(address, size=0x120, label=""):
        print(f"\n--- disasm {label} va=0x{address:X} rva=0x{address-base:X} ---")
        data = image[off(address):off(address)+size]
        if md:
            for insn in md.disasm(data, address):
                print(f"0x{insn.address:X}: {insn.mnemonic:8s} {insn.op_str}")
        else:
            print(data.hex(" "))

    # Candidate from find_luau
    disasm(va(0x4254540), 0x180, "luau_deserialize candidate")
    # luaD_pcall candidates
    for rva in (0x2697080, 0x2690870):
        disasm(va(rva), 0x100, "luaD_pcall candidate")

    # Find Lua C library registration tables for "create", "resume", "pcall", "yield".
    for name in (b"create", b"resume", b"yield", b"pcall", b"status", b"wrap"):
        # Use the first occurrence in .rdata only, and collect all exact string VAs.
        positions = []
        start = 0
        while True:
            i = image.find(name + b"\0", start)
            if i < 0:
                break
            positions.append(base + i)
            start = i + 1
        print(f"\nname {name!r}: {len(positions)} exact strings")
        for string_va in positions[:20]:
            needle = struct.pack("<Q", string_va)
            start = 0
            table_entries = []
            while True:
                i = image.find(needle, start)
                if i < 0:
                    break
                entry_va = base + i
                if i + 16 <= len(image):
                    func = struct.unpack_from("<Q", image, i + 8)[0]
                    if base <= func < base + module.size:
                        table_entries.append((entry_va, func))
                start = i + 1
            for entry_va, func in table_entries[:5]:
                print(f"  table entry 0x{entry_va:X} (rva 0x{entry_va-base:X}) -> func 0x{func:X} (rva 0x{func-base:X})")
