import io
import tokenize
from pathlib import Path

p = Path(r"C:\Users\SystemX\Desktop\SteamAccGen\SteamAccGen.py")
src = p.read_text(encoding="utf-8")
lines = src.splitlines()

cuts = {}
for t in tokenize.generate_tokens(io.StringIO(src).readline):
    if t.type == tokenize.COMMENT:
        cuts.setdefault(t.start[0], []).append((t.start[1], t.end[1]))

out = []
removed_lines = 0
stripped_inline = 0

for idx, line in enumerate(lines, 1):
    spans = cuts.get(idx)
    if not spans:
        out.append(line)
        continue

    start_col = min(s[0] for s in spans)
    before = line[:start_col]

    if before.strip() == "":
        removed_lines += 1
        continue

    out.append(before.rstrip())
    stripped_inline += 1

new_src = "\n".join(out) + "\n"
p.write_text(new_src, encoding="utf-8")

print("comment-only lines removed:", removed_lines)
print("inline comments stripped:", stripped_inline)
print("old lines:", len(lines), "new lines:", len(out))
