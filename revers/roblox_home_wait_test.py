import sys
import time

sys.path.insert(0, r"C:\Users\SystemX\Desktop\RobloxAccountGenerator")

import RobloxAccGen as m
from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_context(locale="en-US").new_page()
    page.goto("https://www.roblox.com/CreateAccount", wait_until="commit", timeout=60000)
    page.wait_for_selector("#signup-username", state="visible", timeout=30000)

    page.evaluate("setTimeout(() => history.pushState({}, '', '/home'), 500)")
    t0 = time.time()
    home = m.wait_for_signup_home(page, timeout=5)
    print("found:", bool(home), "url:", home.url if home else None, f"elapsed={time.time() - t0:.2f}s")
    browser.close()
