from pathlib import Path

for name in ("signup_bundle.js", "signup_small.js"):
    p = Path(r"C:\Users\SystemX\AppData\Local\Temp\opencode") / name
    s = p.read_text(encoding="utf-8", errors="ignore")
    needle = "Birthday must be set first"
    start = 0
    print("=" * 30, name, len(s))
    while True:
        i = s.find(needle, start)
        if i < 0:
            break
        print(f"--- idx {i} ---")
        print(s[max(0, i - 1800):i + 800])
        start = i + 1
