import json
import time

from playwright.sync_api import sync_playwright

FILL_OLD = r"""
(args) => {
    const { username, password, month, day, year } = args;
    const setNative = (el, value) => {
        const proto = el.tagName === 'SELECT' ? window.HTMLSelectElement.prototype : window.HTMLInputElement.prototype;
        Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, value);
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        el.dispatchEvent(new Event('blur', { bubbles: true }));
    };
    const u = document.querySelector('#signup-username');
    const p = document.querySelector('#signup-password');
    const m = document.querySelector('#MonthDropdown');
    const d = document.querySelector('#DayDropdown');
    const y = document.querySelector('#YearDropdown');
    if (!u || !p || !m || !d || !y) return { error: 'fields missing' };
    setNative(u, username);
    setNative(p, password);
    const mo = [...m.options].find(o => o.textContent.trim() === month);
    const dd = [...d.options].find(o => o.textContent.trim() === day);
    const yo = [...y.options].find(o => o.textContent.trim() === year);
    if (mo) setNative(m, mo.value);
    if (dd) setNative(d, dd.value);
    if (yo) setNative(y, yo.value);
    return { ok: true };
}
"""

FILL_NEW = r"""
(args) => {
    const { username, password, month, day, year } = args;
    const setNative = (el, value) => {
        const proto = el.tagName === 'SELECT' ? window.HTMLSelectElement.prototype : window.HTMLInputElement.prototype;
        Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, value);
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
    };
    const u = document.querySelector('#signup-username');
    const p = document.querySelector('#signup-password');
    const m = document.querySelector('#MonthDropdown');
    const d = document.querySelector('#DayDropdown');
    const y = document.querySelector('#YearDropdown');
    if (!u || !p || !m || !d || !y) return { error: 'fields missing' };
    const mo = [...m.options].find(o => o.textContent.trim() === month);
    const dd = [...d.options].find(o => o.textContent.trim() === day);
    const yo = [...y.options].find(o => o.textContent.trim() === year);
    if (mo) setNative(m, mo.value);
    if (dd) setNative(d, dd.value);
    if (yo) setNative(y, yo.value);
    setNative(u, username);
    setNative(p, password);
    return { ok: true };
}
"""

STATE = r"""
() => {
    const btn = document.querySelector('button.signup-submit-button');
    const errors = [...document.querySelectorAll('.input-validation, [role="alert"], [class*="error" i]')]
        .filter(e => e.offsetParent)
        .map(e => (e.innerText || '').trim())
        .filter(Boolean);
    return {
        disabled: btn ? btn.disabled : null,
        errors,
        hasBirthdayError: document.body.innerText.includes('Birthday must be set first'),
        values: {
            month: (document.querySelector('#MonthDropdown') || {}).value,
            day: (document.querySelector('#DayDropdown') || {}).value,
            year: (document.querySelector('#YearDropdown') || {}).value,
            username: (document.querySelector('#signup-username') || {}).value,
        },
    };
}
"""

ARGS = {
    "username": "LLvyLWZLUCA",
    "password": "fFCO6lz0ngtf",
    "month": "January",
    "day": "01",
    "year": "2005",
}


def run_once(pw, script, label, iterations=3):
    for i in range(iterations):
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(locale="en-US")
        page = ctx.new_page()
        t0 = time.time()
        page.goto("https://www.roblox.com/CreateAccount", wait_until="commit", timeout=60000)
        page.wait_for_selector("#signup-username", state="visible", timeout=30000)
        t_visible = time.time() - t0
        hooked = None
        for _ in range(100):
            hooked = page.evaluate(
                "() => { const m = document.querySelector('#MonthDropdown');"
                " const b = document.querySelector('button.signup-submit-button');"
                " const h = el => !!el && Object.keys(el).some(k => k.startsWith('__reactProps$'));"
                " return !!m && !!b && h(m) && h(b); }"
            )
            if hooked:
                break
            page.wait_for_timeout(100)
        t_hooked = time.time() - t0
        page.evaluate(script, ARGS)
        page.wait_for_timeout(2500)
        st = page.evaluate(STATE)
        print(f"[{label}-{i + 1}] visible={t_visible:.2f}s hooked={t_hooked:.2f}s "
              f"disabled={st['disabled']} err={st['errors']} birthday_err={st['hasBirthdayError']}")
        browser.close()


with sync_playwright() as pw:
    run_once(pw, FILL_OLD, "old")
    run_once(pw, FILL_NEW, "new")
