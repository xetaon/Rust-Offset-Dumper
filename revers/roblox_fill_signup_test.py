import sys
import time

sys.path.insert(0, r"C:\Users\SystemX\Desktop\RobloxAccountGenerator")

import RobloxAccGen as m
from playwright.sync_api import sync_playwright

m.BIRTHDAY = ("January", "01", "2005")
m.GENDER = "men"

with sync_playwright() as pw:
    failures = 0
    for i in range(3):
        browser = pw.chromium.launch(headless=True)
        page = browser.new_context(locale="en-US").new_page()
        page.goto("https://www.roblox.com/CreateAccount", wait_until="commit", timeout=60000)
        page.wait_for_selector("#signup-username", state="visible", timeout=30000)
        print(f"=== fill_signup_form run {i + 1} ===")
        t0 = time.time()
        username, password = m.fill_signup_form(page)
        elapsed = time.time() - t0
        state = page.evaluate("""() => {
            const btn = document.querySelector('button.signup-submit-button');
            return {
                disabled: btn ? btn.disabled : null,
                url: location.href,
                username: (document.querySelector('#signup-username') || {}).value,
            };
        }""")
        ok = bool(m.LAST_DOB_VALID and state["disabled"] is False)
        print(f"elapsed={elapsed:.2f}s LAST_DOB_VALID={m.LAST_DOB_VALID} state={state} user={username}")
        print("PASS" if ok else "FAIL")
        if not ok:
            failures += 1
        browser.close()

    print("FAILURES:", failures)
