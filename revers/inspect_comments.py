import io
import tokenize
from pathlib import Path

p = Path(r"C:\Users\SystemX\Desktop\SteamAccGen\SteamAccGen.py")
src = p.read_text(encoding="utf-8")

comments = []
for t in tokenize.generate_tokens(io.StringIO(src).readline):
    if t.type == tokenize.COMMENT:
        comments.append((t.start[0], t.string))

print("total comments:", len(comments))
for line, text in comments[:20]:
    print(line, repr(text[:100]))

docstrings = [i for i, l in enumerate(src.splitlines(), 1)
              if l.strip().startswith('"""') or l.strip().startswith("'''")]
print("docstring lines:", len(docstrings))
