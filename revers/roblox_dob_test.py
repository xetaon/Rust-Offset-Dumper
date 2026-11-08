import json
import time

from playwright.sync_api import sync_playwright

FILL = r"""
(args) => {
    const { username, password, month, day, year, gender, withBlur } = args;
    const setNative = (el, value) => {
        const proto = el.tagName === 'SELECT'
            ? window.HTMLSelectElement.prototype
            : window.HTMLInputElement.prototype;
        const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
        setter.call(el, value);
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        if (withBlur) el.dispatchEvent(new Event('blur', { bubbles: true }));
    };
    const q = id => document.querySelector(id);
    const monthEl = q('#MonthDropdown');
    const daySel = q('#DayDropdown');
    const yearSel = q('#YearDropdown');
    const nameEl = q('#signup-username');
    const passEl = q('#signup-password');
    if (!monthEl || !daySel || !yearSel || !nameEl || !passEl) {
        return { error: 'fields missing' };
    }
    if (nameEl) setNative(nameEl, username);
    if (passEl) setNative(passEl, password);
    const m = [...monthEl.options].find(o => o.textContent.trim() === month);
    const d = [...daySel.options].find(o => o.textContent.trim() === day);
    const y = [...yearSel.options].find(o => o.textContent.trim() === year);
    if (m) setNative(monthEl, m.value);
    if (d) setNative(daySel, d.value);
    if (y) setNative(yearSel, y.value);
    return {
        values: { month: monthEl.value, day: daySel.value, year: yearSel.value },
        found: { month: !!m, day: !!d, year: !!y },
    };
}
"""

STATE = r"""
() => {
    const btn = document.querySelector('button.signup-submit-button')
        || [...document.querySelectorAll('button')].find(b => (b.innerText || '').trim().toLowerCase().startsWith('sign up'));
    const errors = [...document.querySelectorAll('.input-validation, [role="alert"], [class*="error" i]')]
        .filter(e => e.offsetParent)
        .map(e => (e.innerText || '').trim())
        .filter(Boolean);
    const reactReady = el => {
        if (!el) return false;
        const k = Object.keys(el).find(k => k.startsWith('__reactProps$'));
        return !!(k && el[k] && typeof el[k].onChange === 'function');
    };
    const m = document.querySelector('#MonthDropdown');
    return {
        disabled: btn ? btn.disabled : null,
        errors,
        reactReady: reactReady(m),
        values: {
            month: m ? m.value : null,
            day: (document.querySelector('#DayDropdown') || {}).value,
            year: (document.querySelector('#YearDropdown') || {}).value,
        },
        bodyHasBirthdayError: document.body.innerText.includes('Birthday must be set first'),
    };
}
"""


def run_once(pw, with_blur, label):
    browser = pw.chromium.launch(headless=True)
    ctx = browser.new_context(locale="en-US")
    page = ctx.new_page()
    page.goto("https://www.roblox.com/CreateAccount", wait_until="commit", timeout=60000)
    page.wait_for_selector("#signup-username", state="visible", timeout=30000)
    ready = page.evaluate(
        "() => { const m = document.querySelector('#MonthDropdown'); if (!m) return {sel:false, react:false};"
        " const k = Object.keys(m).find(k => k.startsWith('__reactProps$'));"
        " return {sel:true, react: !!(k && m[k] && typeof m[k].onChange === 'function')}; }"
    )
    t0 = time.time()
    out = page.evaluate(FILL, {
        "username": "LLvyLWZLUCA",
        "password": "fFCO6lz0ngtf",
        "month": "January",
        "day": "01",
        "year": "2005",
        "gender": "men",
        "withBlur": with_blur,
    })
    page.wait_for_timeout(1500)
    state = page.evaluate(STATE)
    print(f"[{label}] ready={ready} fill={out} elapsed={time.time() - t0:.2f}s")
    print(f"[{label}] state={json.dumps(state, ensure_ascii=False)}")
    browser.close()


with sync_playwright() as pw:
    for i in range(2):
        run_once(pw, True, f"blur-{i + 1}")
    for i in range(2):
        run_once(pw, False, f"noblur-{i + 1}")
