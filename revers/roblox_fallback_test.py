import random
import string
import sys
import time

sys.path.insert(0, r"C:\Users\SystemX\Desktop\RobloxAccountGenerator")

import RobloxAccGen as m
from playwright.sync_api import sync_playwright

m.BIRTHDAY = ("January", "01", "2005")

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_context(locale="en-US").new_page()
    page.goto("https://www.roblox.com/CreateAccount", wait_until="commit", timeout=60000)
    page.wait_for_selector("#signup-username", state="visible", timeout=30000)

    # Break the well-known IDs so only the generic detection can find the fields.
    page.evaluate("""() => {
        const rename = (oldId, newId) => {
            const el = document.getElementById(oldId);
            if (el) { el.id = newId; }
        };
        rename('MonthDropdown', 'XMonth');
        rename('DayDropdown', 'XDay');
        rename('YearDropdown', 'XYear');
        rename('signup-username', 'XUser');
        rename('signup-password', 'XPass');
    }""")

    user = "FallbackTest" + "".join(random.choices(string.ascii_lowercase, k=4))
    t0 = time.time()
    result = m.fill_form_fast(page, user, "QaPass12345", "none")
    elapsed = time.time() - t0
    state = page.evaluate("""() => {
        const btn = document.querySelector('button.signup-submit-button');
        return {
            disabled: btn ? btn.disabled : null,
            username: (document.getElementById('XUser') || {}).value,
            month: (document.getElementById('XMonth') || {}).value,
            day: (document.getElementById('XDay') || {}).value,
            year: (document.getElementById('XYear') || {}).value,
        };
    }""")
    print(f"elapsed={elapsed:.2f}s result=", {k: result.get(k) for k in ("name", "pass", "month", "day", "year", "gender", "dob_valid", "form_ready")} if result else None)
    print("LAST_DOB_VALID:", m.LAST_DOB_VALID, "state:", state)
    browser.close()
