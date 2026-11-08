import ctypes, os, winreg
from pathlib import Path

ttf = Path(r"C:\Windows\Fonts\lanapixel-regular.ttf")
log = []

# 1. выгрузить из GDI текущей сессии
try:
    removed = ctypes.windll.gdi32.RemoveFontResourceW(str(ttf))
    log.append(f"RemoveFontResourceW: {removed}")
except Exception as e:
    log.append(f"RemoveFontResourceW error: {e}")

# 2. удалить файл
if ttf.exists():
    try:
        os.remove(ttf)
        log.append("file deleted")
    except OSError as e:
        log.append(f"file delete failed: {e}")

# 3. реестр шрифтов HKLM/HKCU
for root, label in ((winreg.HKEY_LOCAL_MACHINE, "HKLM"), (winreg.HKEY_CURRENT_USER, "HKCU")):
    try:
        with winreg.OpenKey(root, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts",
                            0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, "LanaPixel (TrueType)")
            log.append(f"{label} Fonts value deleted")
    except FileNotFoundError:
        log.append(f"{label} Fonts value absent")
    except OSError as e:
        log.append(f"{label} Fonts delete error: {e}")

# 4. слот консоли 000
for root, label in ((winreg.HKEY_CURRENT_USER, "HKCU"), (winreg.HKEY_LOCAL_MACHINE, "HKLM")):
    try:
        with winreg.OpenKey(root, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Console\TrueTypeFont",
                            0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, "000")
            log.append(f"{label} Console 000 deleted")
    except FileNotFoundError:
        log.append(f"{label} Console 000 absent")
    except OSError as e:
        log.append(f"{label} Console 000 error: {e}")

# 5. broadcast
try:
    ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001D, 0, 0, 0x0002, 1000, ctypes.byref(ctypes.c_ulong()))
except Exception:
    pass

print("\n".join(log))
