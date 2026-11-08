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
        errors: [...document.querySelectorAll('.input-validation, [role="alert"], [class*="error" i]')]
            .filter(e => e.offsetParent).map(e => (e.innerText || '').trim()).filter(Boolean),
    };
}
"""


def username():
    return "QAtest" + "".join(random.choices(string.ascii_letters + string.digits, k=8))


with sync_playwright() as pw:
    for i in range(3):
        browser = pw.chromium.launch(headless=True)
        page = browser.new_context(locale="en-US").new_page()
        page.goto("https://www.roblox.com/CreateAccount", wait_until="commit", timeout=60000)
        page.wait_for_selector("#signup-username", state="visible", timeout=30000)
        m.wait_for_signup_form(page)
        t0 = time.time()
        ok = m.fill_signup_fields_native(page, username(), "QaPass12345")
        ready = m.wait_for_signup_button(page, timeout=6000)
        elapsed = time.time() - t0
        print(f"[native-{i + 1}] fill={ok} ready={ready} elapsed={elapsed:.2f}s state={page.evaluate(CHECK)}")
        browser.close()
