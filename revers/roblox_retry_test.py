import sys
import time

sys.path.insert(0, r"C:\Users\SystemX\Desktop\RobloxAccountGenerator")

import RobloxAccGen as m
from playwright.sync_api import sync_playwright

m.BIRTHDAY = ("January", "01", "2005")
m.GENDER = "men"

NAMES = ["QAtestlgYT2ck2", "BlueFoxrmnof", "NightOwlRetry1"]
name_iter = iter(NAMES)
m.random_username = lambda: next(name_iter, "FinalName" + str(int(time.time())))
m.random_password = lambda: "QaPass12345"

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_context(locale="en-US").new_page()
    page.goto("https://www.roblox.com/CreateAccount", wait_until="commit", timeout=60000)
    page.wait_for_selector("#signup-username", state="visible", timeout=30000)

    t0 = time.time()
    username, password = m.fill_signup_form(page)
    elapsed = time.time() - t0
    state = page.evaluate("""() => {
        const btn = document.querySelector('button.signup-submit-button');
        return {
            disabled: btn ? btn.disabled : null,
            errors: [...document.querySelectorAll('.input-validation, [role="alert"]')]
                .filter(e => e.offsetParent).map(e => (e.innerText || '').trim()).filter(Boolean),
        };
    }""")
    print(f"elapsed={elapsed:.2f}s LAST_DOB_VALID={m.LAST_DOB_VALID} user={username} state={state}")
    browser.close()
