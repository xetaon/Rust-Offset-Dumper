import sys, struct
sys.path.insert(0, r"C:\Users\SystemX\Desktop\Galaxy.Clinic Executor\scripts")
from galaxy.winmem import open_process, ProcessMemoryError, enable_debug_privilege
from galaxy.pe import PEImage
from galaxy.luau_finder import _scan_rip_xrefs_in_bytes

enable_debug_privilege()
PID = 10264
PATH = r"C:\Program Files\Roblox\Versions\version-9ac8595712b447a7\RobloxPlayerBeta.exe"
im = PEImage.from_path(PATH)


def read_image(process, module):
    image = bytearray(module.size)
    missing = 0
    for region in process.module_regions(module):
        delta = region.base - module.base
        if delta < 0 or delta >= module.size:
            continue
        amount = min(region.size, module.size - delta)
        cursor = 0
        while cursor < amount:
            size = min(0x10000, amount - cursor)
            try:
                data = process.read(region.base + cursor, size)
                start = region.base + cursor - module.base
                image[start:start + len(data)] = data
            except ProcessMemoryError:
                page = 0
                while page < size:
                    psize = min(0x1000, size - page)
                    try:
                        data = process.read(region.base + cursor + page, psize)
                        start = region.base + cursor + page - module.base
                        image[start:start + len(data)] = data
                    except ProcessMemoryError:
                        missing += psize
                    page += psize
            cursor += size
    return bytes(image), missing


with open_process(PID) as process:
    module = process.module("RobloxPlayerBeta.exe")
    image, missing = read_image(process, module)
    base = module.base
    print("image", len(image), "missing", missing)

    def rva_of(addr):
        return addr - base

    def cstr(offset, limit=200):
        end = image.find(b"\0", offset, offset + limit)
        if end < 0:
            return None
        raw = image[offset:end]
        if not raw:
            return None
        try:
            text = raw.decode("ascii")
        except UnicodeDecodeError:
            return None
        if not all(32 <= ord(ch) < 127 or ch in "\t" for ch in text):
            return None
        return text

    print("\n=== strings around 0x7283600 ===")
    start = 0x7283600
    end = 0x7283800
    cursor = start
    while cursor < end:
        text = cstr(cursor)
        if text and len(text) >= 4:
            print(f"0x{cursor:X}: {text!r}")
            cursor += len(text) + 1
        else:
            cursor += 1

    print("\n=== xrefs to every candidate start in 0x7283600..0x7283800 ===")
    for candidate in range(start, end):
        if image[candidate] < 32 or image[candidate] > 126:
            continue
        if candidate > 0 and image[candidate - 1] != 0:
            continue
        target = base + candidate
        xrefs = list(_scan_rip_xrefs_in_bytes(image, base, target))
        if xrefs:
            print(f"0x{candidate:X} {cstr(candidate)!r} -> " + ", ".join(f"0x{rva_of(x.address):X}" for x in xrefs))

    print("\n=== disasm around RSB1 xref 0x4255e35 ===")
    try:
        import capstone
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
        md.detail = True
    except Exception as exc:
        print("no capstone", exc)
        md = None

    def disasm(start_rva, size, label):
        print(f"\n--- {label} rva=0x{start_rva:X} ---")
        data = image[start_rva:start_rva + size]
        cursor = start_rva
        if md:
            for insn in md.disasm(data, base + start_rva):
                marker = ""
                if insn.mnemonic in ("call", "lea", "mov", "cmp") and "rip" in insn.op_str:
                    marker = "  <-- rip"
                print(f"0x{insn.address-base:X}: {insn.mnemonic:8s} {insn.op_str}{marker}")
        else:
            print(data.hex(" "))

    disasm(0x4255C80, 0x300, "RSB1 reference")

    print("\n=== luaL_Reg-style tables in 0x6A3F000..0x6A42000 ===")
    tables = {}
    lower = 0x6A3F000
    upper = 0x6A42000
    offset = lower
    while offset + 16 <= upper:
        name_ptr = struct.unpack_from("<Q", image, offset)[0]
        func_ptr = struct.unpack_from("<Q", image, offset + 16 - 16 + 0)
        func_ptr = struct.unpack_from("<Q", image, offset + 8)[0]
        if base <= name_ptr < base + module.size and base <= func_ptr < base + module.size:
            name_off = name_ptr - base
            text = cstr(name_off)
            if text is not None and 1 <= len(text) <= 40:
                tables.setdefault(offset, []).append((text, func_ptr))
        offset += 16

    # Group contiguous tables: entries usually 16 bytes apart.
    groups = []
    current = []
    for offset in sorted(tables):
        if current and offset == current[-1] + 16:
            current.append(offset)
        else:
            if current:
                groups.append(current)
            current = [offset]
    if current:
        groups.append(current)
    for group in groups:
        if len(group) < 2:
            continue
        print(f"\n--- table at rva 0x{group[0]:X} ({len(group)} entries) ---")
        for offset in group:
            for text, func_ptr in tables[offset]:
                print(f"  0x{offset:X}  {text:24s} -> 0x{func_ptr-base:X}")

    print("\n=== search all tables containing pcall/resume/create/yield/wrap/status anywhere ===")
    wanted = {"pcall", "resume", "create", "yield", "wrap", "status", "close", "isyieldable", "running"}
    seen = set()
    offset = 0
    while offset + 16 <= len(image) - 16:
        name_ptr = struct.unpack_from("<Q", image, offset)[0]
        if base <= name_ptr < base + module.size:
            text = cstr(name_ptr - base, 32)
            if text in wanted and text not in seen:
                func_ptr = struct.unpack_from("<Q", image, offset + 8)[0]
                if base <= func_ptr < base + module.size:
                    print(f"0x{offset:X} rva 0x{offset:X} {text:12s} -> 0x{func_ptr-base:X} (entry 0x{offset:X})")
                    seen.add(text)
        offset += 8
