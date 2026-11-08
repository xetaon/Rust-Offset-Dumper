import sys, struct
sys.path.insert(0, r"C:\Users\SystemX\Desktop\Galaxy.Clinic Executor\scripts")
import numpy as np
from galaxy.winmem import open_process, ProcessMemoryError, enable_debug_privilege
from galaxy.pe import PEImage
import capstone

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

    def all_rip_hits(target_rva):
        hits = []
        total = len(image)
        chunk = 32 * 1024 * 1024
        start = 0
        while start < total:
            end = min(total, start + chunk + 8)
            for shift in range(4):
                begin = start + shift
                stop = min(end, total)
                count = (stop - begin) // 4
                if count <= 0:
                    continue
                arr = np.frombuffer(image, dtype="<u4", count=count, offset=begin)
                positions = np.arange(arr.size, dtype=np.int64) * 4 + begin
                match = np.nonzero(arr.astype(np.int64) + positions == target_rva - 4)[0]
                for index in match:
                    hits.append(int(positions[index]))
            start += chunk
        return sorted(set(hits))

    print("\n=== per-byte rip xref scan over string regions ===")
    for region_start, region_end, label in [
        (0x72836E0, 0x72837C8, "resume/error strings"),
        (0x7284780, 0x72848A0, "base library name strings"),
        (0x73E6A80, 0x73E6B40, "pcall context 1"),
        (0x73F2DC0, 0x73F2E60, "pcall context 2"),
    ]:
        print(f"\n-- {label} --")
        seen = set()
        for position in range(region_start, region_end):
            hits = all_rip_hits(position)
            for hit in hits:
                key = (position, hit)
                if key in seen:
                    continue
                seen.add(key)
                print(f"  ref 0x{hit:X} (instr ends 0x{hit+4:X}) -> 0x{position:X}")

    print("\n=== ASCII chunks of resume strings inside .text ===")
    text_start, text_size = 0x1000, 0x643358C
    text = image[text_start:text_start + text_size]
    for string in (b"cannot resume dead coroutine", b"cannot resume non-suspended coroutine",
                   b"cannot resume ", b"dead coroutine", b"non-suspended coroutine"):
        hits = []
        cursor = 0
        while True:
            index = text.find(string, cursor)
            if index < 0:
                break
            hits.append(text_start + index)
            cursor = index + 1
        print(f"  {string!r}: {[hex(h) for h in hits[:20]]}")
    for string in (b"cannot r", b"esume de", b"ad corou", b"tine"):
        chunk = string.ljust(8, b"\0")[:8]
        value = struct.pack("<Q", struct.unpack("<Q", chunk)[0])
        hits = []
        cursor = 0
        while True:
            index = image.find(value, cursor)
            if index < 0:
                break
            if text_start <= index < text_start + text_size:
                hits.append(index)
            cursor = index + 1
        print(f"  immediate {string!r}: {[hex(h) for h in hits[:20]]}")

    print("\n=== raw base-library table near 0x67dcb00 ===")
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

    for offset in range(0x67dcb00, 0x67dce40, 16):
        name_ptr, func_ptr = struct.unpack_from("<QQ", image, offset)
        text = None
        if base <= name_ptr < base + module.size:
            text = cstr(name_ptr - base, 64)
        func_rva = func_ptr - base if base <= func_ptr < base + module.size else None
        print(f"0x{offset:X} name=0x{name_ptr:X} {text!r} func=" + (f"0x{func_rva:X}" if func_rva is not None else "0x0"))

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

    full(0x59E9BD0, 0x120, "luaD_pcall candidate")
    full(0x59EB430, 0x160, "function before error-in-error-handling copy")

    print("\n=== function boundaries in 0x59EA000..0x59EC900 ===")
    cursor = 0x59EA000
    limit = 0x59EC900
    while cursor < limit:
        run = 0
        probe = cursor
        while probe < limit and image[probe] in (0xCC,):
            run += 1
            probe += 1
        if run >= 2:
            print(f"  padding {run} at 0x{cursor:X} .. 0x{probe:X}")
            cursor = probe
            continue
        cursor += 1
