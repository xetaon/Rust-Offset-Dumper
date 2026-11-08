import random
import string
import sys

sys.path.insert(0, r"C:\Users\SystemX\Desktop\RobloxAccountGenerator")

import RobloxAccGen as m
from playwright.sync_api import sync_playwright

m.BIRTHDAY = ("January", "01", "2005")

CHECK = r"""
() => {
    const btn = document.querySelector('button.signup-submit-button');
    const errors = [...document.querySelectorAll('.input-validation, [role="alert"], [class*="error" i]')]
        .filter(e => e.offsetParent)
        .map(e => (e.innerText || '').trim())
        .filter(Boolean);
    return {
        disabled: btn ? btn.disabled : null,
        errors,
        values: {
            month: (document.querySelector('#MonthDropdown') || {}).value,
            day: (document.querySelector('#DayDropdown') || {}).value,
            year: (document.querySelector('#YearDropdown') || {}).value,
            username: (document.querySelector('#signup-username') || {}).value,
            password_len: ((document.querySelector('#signup-password') || {}).value || '').length,
        },
    };
}
"""


def username():
    return "QAtest" + "".join(random.choices(string.ascii_letters + string.digits, k=8))


with sync_playwright() as pw:
    failures = 0
    for i in range(3):
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(locale="en-US")
        page = context.new_page()
        page.goto("https://www.roblox.com/CreateAccount", wait_until="commit", timeout=60000)
        page.wait_for_selector("#signup-username", state="visible", timeout=30000)

        user = username()
        password = "QaPass" + str(random.randint(10000, 99999))
        print(f"=== run {i + 1}: {user} ===")
        result = m.fill_form_fast(page, user, password, "men")
        state = page.evaluate(CHECK)
        print("result:", {k: result.get(k) for k in ("name", "pass", "month", "day", "year", "gender", "dob_valid", "form_ready")} if result else None)
        print("LAST_DOB_VALID:", m.LAST_DOB_VALID)
        print("state:", state)
        ok = bool(result and result.get("form_ready") and m.LAST_DOB_VALID and state["disabled"] is False and not state["errors"])
        print("PASS" if ok else "FAIL")
        if not ok:
            failures += 1
        browser.close()

    print("FAILURES:", failures)
