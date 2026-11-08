import random
import string
import sys
import time

sys.path.insert(0, r"C:\Users\SystemX\Desktop\RobloxAccountGenerator")

import RobloxAccGen as m
from playwright.sync_api import sync_playwright

m.BIRTHDAY = ("January", "01", "2005")

CHECK = r"""
() => {
    const btn = document.querySelector('button.signup-submit-button');
    return {
        disabled: btn ? btn.disabled : null,
        errors: [...document.querySelectorAll('.input-validation, [role="alert"]',)]
            .filter(e => e.offsetParent).map(e => (e.innerText || '').trim()).filter(Boolean),
        values: {
            month: (document.querySelector('#MonthDropdown') || {}).value,
            day: (document.querySelector('#DayDropdown') || {}).value,
            year: (document.querySelector('#YearDropdown') || {}).value,
        },
    };
}
"""

PREFIXES = ["NightOwl", "BlueFox", "SilverRay", "MoonWolf", "StarHawk"]


def username(i):
    return PREFIXES[i % len(PREFIXES)] + "".join(random.choices(string.ascii_lowercase, k=5))


with sync_playwright() as pw:
    failures = 0
    for i in range(5):
        browser = pw.chromium.launch(headless=True)
        page = browser.new_context(locale="en-US").new_page()
        page.goto("https://www.roblox.com/CreateAccount", wait_until="commit", timeout=60000)
        page.wait_for_selector("#signup-username", state="visible", timeout=30000)

        user = username(i)
        password = "QaPass" + str(random.randint(10000, 99999))
        print(f"=== run {i + 1}: {user} ===")
        t0 = time.time()
        result = m.fill_form_fast(page, user, password, "men")
        elapsed = time.time() - t0
        state = page.evaluate(CHECK)
        print(f"elapsed={elapsed:.2f}s result=", {k: result.get(k) for k in ("name", "pass", "month", "day", "year", "gender", "dob_valid", "form_ready")} if result else None)
        print("LAST_DOB_VALID:", m.LAST_DOB_VALID, "state:", state)
        ok = bool(result and result.get("form_ready") and m.LAST_DOB_VALID and state["disabled"] is False and not state["errors"])
        print("PASS" if ok else "FAIL")
        if not ok:
            failures += 1
        browser.close()

    print("FAILURES:", failures)
