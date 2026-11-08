import sys, struct
sys.path.insert(0, r"C:\Users\SystemX\Desktop\Galaxy.Clinic Executor\scripts")
from galaxy.winmem import open_process, ProcessMemoryError, enable_debug_privilege
from galaxy.pe import PEImage
import capstone

enable_debug_privilege()
PID = int(sys.argv[1]) if len(sys.argv) > 1 else 0
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

    text_start, text_size = 0x1000, 0x643358C

    def cstr(offset, limit=120):
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

    print("\n=== strings 0x7284700..0x7284A00 ===")
    cursor = 0x7284700
    while cursor < 0x7284A00:
        text = cstr(cursor)
        if text and len(text) >= 2:
            print(f"0x{cursor:X}: {text!r}")
            cursor += len(text) + 1
        else:
            cursor += 1

    def callers(target):
        result = []
        start = text_start
        end = text_start + text_size - 5
        cursor = start
        while True:
            index = image.find(b"\xe8", cursor, end)
            if index < 0:
                break
            cursor = index + 1
            displacement = struct.unpack_from("<i", image, index + 1)[0]
            if index + 5 + displacement == target:
                result.append(index)
        return result

    targets = {
        "rsb1_decoder_0x4255D30": 0x4255D30,
        "luaD_pcall_0x59E9BD0": 0x59E9BD0,
        "sub_0x268CFF0": 0x268CFF0,
        "luaD_pcall_alt_0x2697080": 0x2697080,
        "sub_0x2690870": 0x2690870,
        "cocreate_0x59EA830": 0x59EA830,
        "yield_0x59EB010": 0x59EB010,
        "close_0x59EB170": 0x59EB170,
    }
    for name, target in targets.items():
        hits = callers(target)
        print(f"\ncallers of {name}: {[hex(h) for h in hits[:40]]}")
        for hit in hits[:12]:
            print(f"  from 0x{hit:X}")

    print("\n=== function candidates around 0x53FB000 (prologues + padding) ===")
    for position in range(0x53FB000, 0x53FB600):
        if image[position] == 0xCC:
            run_start = position
            while position < 0x53FB600 and image[position] == 0xCC:
                position += 1
            if position - run_start >= 2:
                print(f"  padding {position-run_start} 0x{run_start:X}..0x{position:X}")
        elif image[position] == 0xF3 and image[position:position + 4] == b"\xf3\x0f\x1e\xfa":
            print(f"  endbr64 0x{position:X}")
    # Find nearest preceding prologue-ish boundary before the two xrefs.
    for needle in (b"\x48\x89\x5c\x24\x08", b"\x48\x89\x5c\x24\x10", b"\x48\x89\x74\x24\x08",
                   b"\x48\x8b\xc4", b"\x40\x53", b"\x40\x55", b"\x48\x83\xec"):
        index = image.rfind(needle, 0x53FA000, 0x53FB3EC)
        if index >= 0:
            print(f"  last {needle.hex(' ')} before xref: 0x{index:X}")

    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True

    def disasm(start_rva, size, label, full=False):
        print(f"\n--- {label} 0x{start_rva:X} ---")
        data = image[start_rva:start_rva + size]
        for insn in md.disasm(data, base + start_rva):
            rva = insn.address - base
            note = ""
            if "rip" in insn.op_str:
                try:
                    detail = insn.operands[1]
                    target = insn.address + insn.size + detail.mem.disp
                    string = cstr(target - base)
                    note = f" -> 0x{target-base:X}" + (f" {string!r}" if string else "")
                except Exception:
                    pass
            if full or insn.mnemonic in ("call", "jmp", "ret", "int3", "endbr64") or "rip" in insn.op_str:
                print(f"0x{rva:X}: {insn.mnemonic:8s} {insn.op_str}{note}")

    disasm(0x53FB1C0, 0x340, "resume candidate", full=False)
    # Determine where the function really begins: try from 0x53FB000.
    disasm(0x53FB000, 0x80, "resume candidate entry probe", full=True)

    print("\n=== callers of RSB1 decoder disassembly ===")
    for hit in callers(0x4255D30)[:20]:
        disasm(hit - 0x80, 0x120, f"caller at 0x{hit:X}", full=False)
