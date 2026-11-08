import re
import sqlite3
import shutil
import tempfile
from pathlib import Path

prof = Path(r"C:\Users\SystemX\Desktop\SteamAccGen\ChromeProfiles\SteamProfile\Default")
tmp = Path(tempfile.mkdtemp(prefix="chromecheck2_"))

for name in ["Network/Cookies", "Network/TransportSecurity"]:
    src = prof / name
    if not src.exists():
        print(name, "(нет)")
        continue
    dst = tmp / (name.replace("/", "_") + ".db")
    shutil.copy2(src, dst)
    try:
        con = sqlite3.connect(dst)
        tbl = con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        print(f"== {name} tables: {tbl}")
        if "cookies" in [t[0] for t in tbl]:
            rows = con.execute("SELECT host_key, name, length(encrypted_value) FROM cookies").fetchall()
            print(f"   cookies: {len(rows)}")
            for r in rows[:60]:
                print("   ", r)
        con.close()
    except Exception as exc:
        print(name, "ERR", exc)

sync = prof / "Sync Data"
print("\n== Sync Data ==")
if sync.exists():
    for p in sync.rglob("*"):
        if p.is_file():
            print("   file:", p.name, p.stat().st_size)

print("\n== строки с gmail/@/google accounts в Sync Data ==")
if sync.exists():
    for p in sync.rglob("*"):
        if not p.is_file():
            continue
        data = p.read_bytes()
        text = data.decode("latin-1", "ignore")
        for m in re.finditer(r"[ -~]{6,}", text):
            s = m.group(0)
            low = s.lower()
            if "gmail" in low or "google.com" in low or "@" in s and "accounts" in low:
                print(f"   [{p.name}] {s[:200]}")

print("\n== Local State: профиль/аккаунты ==")
ls = Path(r"C:\Users\SystemX\Desktop\SteamAccGen\ChromeProfiles\SteamProfile\Local State")
if ls.exists():
    t = ls.read_text(encoding="utf-8", errors="ignore")
    for m in re.finditer(r'"(account_info|email|user_name|gaia|full_name)"\s*:\s*("[^"]*"|\[[^\]]*\])', t):
        print("   ", m.group(0)[:200])

shutil.rmtree(tmp, ignore_errors=True)
