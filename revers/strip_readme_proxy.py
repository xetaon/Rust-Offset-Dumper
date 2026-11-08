from pathlib import Path

p = Path(r"C:\Users\SystemX\Desktop\SteamAccGen\README.md")
s = p.read_text(encoding="utf-8")


def cut(text, start, end):
    i = text.index(start)
    j = text.index(end, i)
    print(f"cut {i}..{j}")
    return text[:i] + text[j:]


s = cut(s, "### 3. Прокси", "### 4. Аватар")
s = s.replace("### 4. Аватар", "### 3. Аватар")
s = s.replace("  - [3. Прокси](#3-прокси)\n", "")
s = s.replace(
    "- 🌐 Проверка прокси на живость (до 50 потоков) и перебор рабочих прокси с авто-откатом на прямое соединение.\n",
    "")
s = s.replace(
    "- 🕵️ Определение ошибки «Steam обнаружил VPN/прокси» и автоматическая смена прокси.\n",
    "")
s = s.replace("| Прокси (опционально) | HTTP / SOCKS4 / SOCKS5 |\n", "")
s = s.replace(
    "4. Пройдите настройку ниже (NoneCap + Gmail + при необходимости прокси).",
    "4. Пройдите настройку ниже (NoneCap + Gmail).")
s = s.replace(
    "При старте: загружаются настройки, создаются папки `ChromeProfiles`, `Proxy` и `Avatar` (с пустым `Proxy/proxy.txt`, если файла не было), удаляются старые профили Chrome, пишется статус прокси и аватара — и открывается главное меню.",
    "При старте: загружаются настройки, создаются папки `ChromeProfiles` и `Avatar`, удаляются старые профили Chrome — и открывается главное меню.")
s = cut(s, "├── Proxy/", "├── Avatar/")
s = cut(s, "1. `build_proxy_list()`", "### Ожидание полной загрузки страниц")
s = s.replace("### Ожидание полной загрузки страниц",
              """1. `launch_chrome_with_cdp()` — запускает Chrome с `--user-data-dir=ChromeProfiles/SteamProfile` и `--remote-debugging-port=<свободный порт>`.
2. Playwright подключается к этому Chrome через `connect_over_cdp`.
3. Открывается `https://store.steampowered.com/join`: заполняется e-mail (дважды), ставится галочка согласия.
4. Ищется hCaptcha `sitekey`, отправляется в NoneCap (`solve(type="hcaptcha")`), полученный токен инжектится в форму (`h-captcha-response`, колбэки виджета).
5. Если форма вернула ошибку — заполнение повторяется до `MAX_FORM_ATTEMPTS` раз.
6. Ожидается confirm-письмо из Gmail (`get_steam_confirm_link`), ссылка открывается в новой вкладке.
7. На странице создаётся логин (8–16 символов) и пароль (12–20, с буквами разного регистра и цифрами).
8. Считывается SteamID64, ставится **AccountName**, затем **аватар** из папки `Avatar/`; строка пишется в `account.txt` и отправляется в Discord.
9. Chrome и временный профиль удаляются — следующий аккаунт начинается с чистого профиля.

### Ожидание полной загрузки страниц""")
s = s.replace(
    "| `STEAM DETECTED PROXY/VPN` | Прокси «грязный» — но такой прокси теперь удаляется из `Proxy/proxy.txt` автоматически; добавьте новых через `Proxy/ProxyParser.exe`. |\n",
    "")
s = s.replace(
    "| `Form error: Произошла ошибка. Повторите попытку позже.` | Steam отдал ошибку уровня прокси — такой прокси **сразу удаляется** (из `Proxy/proxy.txt` и в стоп-лист), попытка переходит к следующему. |\n",
    "")
s = s.replace(
    "Проект использует сторонний сервис решения капчи (NoneCap) — его работоспособность и баланс не входят в этот репозиторий. Папки `GmailAPI/` (секреты OAuth и токен) и `Proxy/`, а также `account.txt` и `ChromeProfiles/` содержат приватные данные и не должны попадать в публичный git.",
    "Проект использует сторонний сервис решения капчи (NoneCap) — его работоспособность и баланс не входят в этот репозиторий. Папки `GmailAPI/` (секреты OAuth и токен), а также `account.txt` и `ChromeProfiles/` содержат приватные данные и не должны попадать в публичный git.")

p.write_text(s, encoding="utf-8")
print("done")
