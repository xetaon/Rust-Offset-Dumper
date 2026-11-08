import sqlite3
import shutil
import tempfile
from pathlib import Path

prof = Path(r"C:\Users\SystemX\Desktop\SteamAccGen\ChromeProfiles\SteamProfile\Default")
tmp = Path(tempfile.mkdtemp(prefix="chromecheck_"))


def dump(name, query):
    src = prof / name
    if not src.exists():
        print(f"{name}: (нет файла)")
        return
    dst = tmp / (name.replace(" ", "_") + ".db")
    shutil.copy2(src, dst)
    try:
        con = sqlite3.connect(dst)
        rows = con.execute(query).fetchall()
        con.close()
        print(f"== {name} ({len(rows)}) ==")
        for r in rows[:40]:
            print("   ", r)
    except Exception as exc:
        print(f"{name}: ERR {exc}")


dump("History", "SELECT url, title, visit_count FROM urls ORDER BY last_visit_time DESC LIMIT 40")
dump("Login Data", "SELECT origin_url, username_value, length(password_value) FROM logins LIMIT 40")
dump("Web Data", "SELECT name, value FROM autofill LIMIT 40")
dump("Cookies", "SELECT host_key, name, length(encrypted_value) FROM cookies LIMIT 60")

print("\n== gmail/steam упоминания в текстовых файлах профиля ==")
for p in prof.rglob("*"):
    if p.is_file() and p.stat().st_size < 5_000_000:
        try:
            t = p.read_bytes().decode("utf-8", "ignore").lower()
        except Exception:
            continue
        for needle in ("gmail", "eheue", "@gmail.com", "mail.google"):
            if needle in t:
                print(f"   {needle}: {p.relative_to(prof)}")
                break

shutil.rmtree(tmp, ignore_errors=True)
