import sys
sys.path.insert(0, r"C:\Users\SystemX\Desktop\SteamAccGen")
import SteamAccGen as m

out = []
out.append(f"face: {m.set_console_font()!r}")
out.append(f"height: {m.CONSOLE_FONT_HEIGHT}")
open(r"C:\Users\SystemX\AppData\Local\Temp\opencode\fonttest2.txt", "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
