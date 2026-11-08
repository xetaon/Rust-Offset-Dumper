import sys
sys.path.insert(0, r"C:\Users\SystemX\Desktop\SteamAccGen")
import SteamAccGen as m

result = []
result.append(f"install: {m.install_console_font()}")
result.append(f"face: {m.set_console_font()!r}")
result.append(f"face16: {m.set_console_font(m.CONSOLE_FONT_NAME, 16)!r}")
open(r"C:\Users\SystemX\AppData\Local\Temp\opencode\fonttest.txt", "w", encoding="utf-8").write("\n".join(result))
print("\n".join(result))
