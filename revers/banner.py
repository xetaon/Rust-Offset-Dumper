import sys
sys.path.insert(0, r"C:\Users\SystemX\Desktop\SteamAccGen")
import SteamAccGen as m
m.COLOR_ENABLED = False
import io
from contextlib import redirect_stdout
buf = io.StringIO()
with redirect_stdout(buf):
    m.print_banner()
    m.print_main_menu()
open(r"C:\Users\SystemX\AppData\Local\Temp\opencode\banner.txt", "w", encoding="utf-8").write(buf.getvalue())
print(repr(buf.getvalue()[:400]))
