import sys, struct
sys.path.insert(0, r"C:\Users\SystemX\Desktop\Galaxy.Clinic Executor\scripts")
import numpy as np
from galaxy.winmem import open_process, ProcessMemoryError, enable_debug_privilege
from galaxy.pe import PEImage
import capstone

enable_debug_privilege()
PID = int(sys.argv[1]) if len(sys.argv) > 1 else 10264
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

    # One pass: find every position P whose following 4-byte displacement D gives
    # P + 4 + D inside one of the interesting string regions.
    regions = [
        (0x7283600, 0x7283900, "resume/error strings"),
        (0x7284700, 0x7284A00, "base library names"),
        (0x73E6A00, 0x73E6C00, "pcall context 1"),
        (0x73F2D00, 0x73F3000, "pcall context 2"),
    ]

    def in_region(value):
        for start, end, label in regions:
            if start <= value < end:
                return label
        return None

    print("\n=== single-pass rip-relative scan ===")
    total = len(image)
    chunk = 32 * 1024 * 1024
    hits = []
    start = 0
    while start < total:
        end = min(total, start + chunk + 8)
        for shift in range(4):
            begin = start + shift
            stop = min(end, total)
            count = (stop - begin) // 4
            if count <= 0:
                continue
            arr = np.frombuffer(image, dtype="<u4", count=count, offset=begin).astype(np.int64)
            positions = np.arange(arr.size, dtype=np.int64) * 4 + begin
            targets = arr + positions + 4
            mask = (targets >= 0x7283000) & (targets < 0x7284A00) | (targets >= 0x73E6000) & (targets < 0x73F3000)
            for index in np.nonzero(mask)[0]:
                region = in_region(int(targets[index]))
                if region:
                    hits.append((int(positions[index]), int(targets[index]), region))
        start += chunk
    hits.sort()
    for position, target, region in hits:
        print(f"  instr_disp 0x{position:X} end 0x{position+4:X} -> 0x{target:X} [{region}]")

    print("\n=== ASCII chunks of resume strings inside .text ===")
    text_start, text_size = 0x1000, 0x643358C
    text = image[text_start:text_start + text_size]
    for string in (b"cannot resume dead coroutine", b"cannot resume non-suspended coroutine",
                   b"cannot resume ", b"dead coroutine", b"non-suspended coroutine", b"Lua function"):
        found = []
        cursor = 0
        while True:
            index = text.find(string, cursor)
            if index < 0:
                break
            found.append(text_start + index)
            cursor = index + 1
        print(f"  {string!r}: {[hex(h) for h in found[:20]]}")

    def cstr(offset, limit=200):
        end = image.find(b"\0", offset, offset + limit)
        if end < 0:
            return None
        raw = image[offset:end]
        if not raw:
            return ""
        try:
            return raw.decode("ascii")
        except UnicodeDecodeError:
            return None

    print("\n=== raw base-library table near 0x67dcb00 ===")
    for offset in range(0x67dcb00, 0x67dce40, 16):
        name_ptr, func_ptr = struct.unpack_from("<QQ", image, offset)
        text_value = None
        if base <= name_ptr < base + module.size:
            text_value = cstr(name_ptr - base, 64)
        func_rva = func_ptr - base if base <= func_ptr < base + module.size else None
        if text_value is None and func_rva is None:
            continue
        print(f"0x{offset:X} name={text_value!r} func=" + (f"0x{func_rva:X}" if func_rva is not None else "0x0"))

    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True

    def full(start_rva, size, label):
        print(f"\n--- {label} 0x{start_rva:X} ---")
        data = image[start_rva:start_rva + size]
        for insn in md.disasm(data, base + start_rva):
            rva = insn.address - base
            note = ""
            if "rip" in insn.op_str:
                try:
                    detail = insn.operands[1]
                    target = insn.address + insn.size + detail.mem.disp
                    string = cstr(target - base, 100)
                    note = f" -> 0x{target-base:X}" + (f" {string!r}" if string else "")
                except Exception:
                    pass
            print(f"0x{rva:X}: {insn.mnemonic:8s} {insn.op_str}{note}")

    full(0x59E9BD0, 0x100, "luaD_pcall candidate")
    full(0x59EB430, 0x180, "before error-in-error-handling copy")

    print("\n=== int3 runs in 0x59EA000..0x59EC900 ===")
    cursor = 0x59EA000
    limit = 0x59EC900
    while cursor < limit:
        if image[cursor] == 0xCC:
            run_start = cursor
            while cursor < limit and image[cursor] == 0xCC:
                cursor += 1
            if cursor - run_start >= 2:
                print(f"  padding {cursor-run_start} at 0x{run_start:X}..0x{cursor:X}")
            continue
        cursor += 1
