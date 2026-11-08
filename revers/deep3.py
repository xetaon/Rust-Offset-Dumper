import sys, struct
sys.path.insert(0, r"C:\Users\SystemX\Desktop\Galaxy.Clinic Executor\scripts")
import numpy as np
from galaxy.winmem import open_process, ProcessMemoryError, enable_debug_privilege
from galaxy.pe import PEImage
from galaxy.luau_finder import _scan_rip_xrefs_in_bytes
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
    print("sections:")
    for section in im.sections:
        print(f"  {section.name:10s} va=0x{section.virtual_address:X} vsize=0x{section.virtual_size:X} raw=0x{section.raw_size:X}")

    def cstr(offset, limit=300):
        if offset < 0 or offset >= len(image):
            return None
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
        if not all(32 <= ord(ch) < 127 or ch == "\t" for ch in text):
            return None
        return text

    def all_rip_xrefs(target_rva, chunk=16 * 1024 * 1024):
        """Scan every byte position with numpy (4 shifts)."""
        hits = []
        total = len(image)
        start = 0
        while start < total:
            end = min(total, start + chunk + 8)
            for shift in range(4):
                begin = start + shift
                if begin >= end:
                    continue
                stop = min(end, total)
                arr = np.frombuffer(image, dtype="<u4", count=(stop - begin) // 4, offset=begin)
                if arr.size == 0:
                    continue
                positions = np.arange(arr.size, dtype=np.int64) * 4 + begin
                match = np.nonzero(arr.astype(np.int64) + positions == target_rva - 4)[0]
                for index in match:
                    hits.append(int(positions[index]))
            start += chunk
        return sorted(set(hits))

    print("\n=== string pointer scan ===")
    terms = [b"pcall", b"xpcall", b"print", b"assert", b"error", b"type", b"tostring", b"tonumber",
             b"cannot resume dead coroutine", b"cannot resume non-suspended coroutine",
             b"attempt to yield across metamethod/C-call boundary",
             b"attempt to break across metamethod/C-call boundary"]
    for term in terms:
        positions = []
        cursor = 0
        while True:
            index = image.find(term + b"\0", cursor)
            if index < 0:
                break
            positions.append(index)
            cursor = index + 1
        print(f"\n{term!r}: {len(positions)} at " + ", ".join(f"0x{p:X}" for p in positions[:10]))
        for pos in positions[:8]:
            text = cstr(pos)
            refs = []
            needle = struct.pack("<Q", base + pos)
            cursor = 0
            while True:
                index = image.find(needle, cursor)
                if index < 0:
                    break
                refs.append(index)
                cursor = index + 1
            print(f"  0x{pos:X} {text!r} qword_refs={[hex(r) for r in refs[:8]]}")

    print("\n=== generic rip scan for resume strings ===")
    for term in (b"cannot resume dead coroutine", b"cannot resume non-suspended coroutine"):
        rva = image.find(term)
        if rva < 0:
            print(term, "not found")
            continue
        hits = all_rip_xrefs(rva)
        print(f"{term!r} rva=0x{rva:X} hits={[(hex(h), hex(h-rva)) for h in hits]}")

    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True

    def resolve_target(operand_text):
        pass

    def describe(start_rva, size, label, full=False):
        print(f"\n--- {label} rva=0x{start_rva:X} ---")
        data = image[start_rva:start_rva + size]
        last_end = start_rva
        for insn in md.disasm(data, base + start_rva):
            rva = insn.address - base
            if rva < last_end:
                continue
            last_end = rva + insn.size
            text = ""
            if insn.mnemonic in ("call", "jmp"):
                text = insn.op_str
            elif "rip" in insn.op_str:
                try:
                    detail = insn.operands[1]
                    target = insn.address + insn.size + detail.mem.disp
                    string = cstr(target - base, 120)
                    text = f"{insn.op_str} -> 0x{target-base:X}" + (f" {string!r}" if string else "")
                except Exception:
                    text = insn.op_str
            else:
                text = insn.op_str
            if full or insn.mnemonic in ("call", "jmp", "ret", "int3") or "rip" in insn.op_str:
                print(f"0x{rva:X}: {insn.mnemonic:8s} {text}")

    describe(0x59EA830, 0x140, "luaB_cocreate", full=True)
    describe(0x59EADA0, 0x180, "luaB_auxwrap", full=True)
    describe(0x59E8DF0, 0x100, "luaB_costatus", full=True)
    describe(0x59E9A00, 0x1200, "resume/pcall region", full=False)
    describe(0x59EB500, 0xE00, "resume/pcall region 2", full=False)
    describe(0x2693000, 0x600, "pcall region 0x2693", full=False)
    describe(0x2697C00, 0x600, "pcall region 0x2697", full=False)

    print("\n=== luaL_Reg tables in non-executable sections with base-library names ===")
    wanted = {b"assert", b"error", b"type", b"print", b"tonumber", b"tostring", b"pcall", b"xpcall",
              b"getmetatable", b"setmetatable", b"rawget", b"rawset", b"rawequal", b"rawlen",
              b"next", b"pairs", b"ipairs", b"select", b"unpack", b"require"}
    for section in im.sections:
        if section.executable:
            continue
        start = section.virtual_address
        end = start + min(section.virtual_size, 64 * 1024 * 1024)
        offset = start
        found = {}
        while offset + 16 <= end:
            b0 = image[offset]
            if 32 <= b0 < 127:
                name_ptr = struct.unpack_from("<Q", image, offset)[0]
                if base <= name_ptr < base + module.size:
                    raw_off = name_ptr - base
                    nul = image.find(b"\0", raw_off, raw_off + 32)
                    if nul > raw_off and image[raw_off:nul] in wanted:
                        func_ptr = struct.unpack_from("<Q", image, offset + 8)[0]
                        if base <= func_ptr < base + module.size:
                            func_section = im.section_for_rva(func_ptr - base)
                            if func_section is not None and func_section.executable:
                                found[offset] = (image[raw_off:nul].decode(), func_ptr - base)
            offset += 16
        if found:
            print(f"\n{section.name}:")
            for offset in sorted(found):
                print(f"  0x{offset:X} {found[offset][0]:14s} -> 0x{found[offset][1]:X}")
