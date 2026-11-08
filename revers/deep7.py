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

    def cstr(offset, limit=160):
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

    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True

    def full(start_rva, size, label):
        print(f"\n--- {label} 0x{start_rva:X} ---")
        data = image[start_rva:start_rva + size]
        last_end = start_rva
        for insn in md.disasm(data, base + start_rva):
            rva = insn.address - base
            if rva < last_end:
                continue
            last_end = rva + insn.size
            note = ""
            if "rip" in insn.op_str:
                try:
                    detail = insn.operands[1]
                    target = insn.address + insn.size + detail.mem.disp
                    string = cstr(target - base)
                    note = f" -> 0x{target-base:X}" + (f" {string!r}" if string else "")
                except Exception:
                    pass
            print(f"0x{rva:X}: {insn.mnemonic:8s} {insn.op_str}{note}")

    full(0x43004B0, 0x300, "ScriptContext::resume")
    full(0x53FB280, 0x300, "candidate referencing resume strings")
    full(0x42560D0, 0x180, "RSB1 decoder caller")

    print("\n=== strings containing bytecode/chunk/load in .rdata ===")
    cursor = 0x6436000
    end = 0x80F0CDE
    found = []
    while cursor < end:
        if image[cursor] == 0:
            cursor += 1
            continue
        text = cstr(cursor)
        if text and len(text) >= 4:
            lowered = text.lower()
            if ("bytecode" in lowered or "load chunk" in lowered or "compiled script" in lowered
                    or "luau_load" in lowered or "deserialize" in lowered or "rsb1" in lowered):
                found.append((cursor, text))
            cursor += len(text) + 1
        else:
            cursor += 1
    print(f"{len(found)} strings")
    for offset, text in found[:120]:
        print(f"0x{offset:X}: {text!r}")

    print("\n=== direct callers of 0x43004B0 ===")
    target = 0x43004B0
    hits = []
    cursor = text_start
    while True:
        index = image.find(b"\xe8", cursor, text_start + text_size - 5)
        if index < 0:
            break
        cursor = index + 1
        if index + 5 + struct.unpack_from("<i", image, index + 1)[0] == target:
            hits.append(index)
    print([hex(h) for h in hits[:40]])
