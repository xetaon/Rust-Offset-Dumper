import sys
sys.dont_write_bytecode = True

import atexit
import base64
import configparser
import ctypes
import html
import json
import os
import random
import re
import select
import shutil
import socket
import socketserver
import ssl
import string
import subprocess
import threading
import time
import traceback
import urllib.parse
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from pathlib import Path
import requests
from playwright.sync_api import sync_playwright
from nonecap import NoneCap

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent

MODULE_NAME = Path(__file__).stem
PROFILE_BASE_DIR = BASE_DIR / "ChromeProfiles"
AVATAR_DIR = BASE_DIR / "Avatar"
AVATAR_EXTENSIONS = (".png", ".jpg", ".jpeg", ".jfif", ".jng", ".gif")
STEAM_URL = "https://store.steampowered.com/join"
CDP_PORT = 9222
HEADLESS_MODE = True
ACCOUNTS_TOTAL = 1
ACCOUNT_GAP = 1
WINDOW_SIZE = "1280,800"
ACCOUNTS_FILE = BASE_DIR / "account.txt"
CONFIG_FILE = BASE_DIR / "SteamAccGen.ini"

# ==== УСКОРЕНИЕ ====
FAST_GOTO = 5000
FAST_CDP_WAIT = 2.0
FAST_CAPTCHA_TIMEOUT = 3000
FAST_EMAIL_TIMEOUT = 4000
FAST_ERR_CHECK = 0.3
FAST_ERR_RETRIES = 2
# Сколько ждать появления полей регистрации, прежде чем закончить попытку
FORM_READY_TIMEOUT = 8000
# Селекторы, по которым видно, что форма регистрации загрузилась
FORM_READY_SELECTOR = "#email, #accountname, #createAccountButton, #i_agree_check"
# Сколько раз повторять заполнение формы, если сайт уже загрузился
MAX_FORM_ATTEMPTS = 5

# Сколько секунд показывать итог перед возвратом в меню.
# 0 = показывать мгновенно и сразу возвращаться.
RESULT_SCREEN_DELAY = 6


PROFILE_DIR = None
PROFILE_NAME = "SteamProfile"

EMAIL_ADDRESS = "your_email@gmail.com"
GMAIL_DIR = BASE_DIR / "GmailAPI"
GMAIL_CREDS_FILE = GMAIL_DIR / "client_secret.json"
GMAIL_TOKEN_FILE = GMAIL_DIR / "token.json"
GMAIL_API = "https://gmail.googleapis.com/gmail/v1/users/me"
GMAIL_TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GMAIL_REDIRECT = "http://localhost:8765/callback"
GMAIL_PORT = 8765
GMAIL_SCOPES = "https://www.googleapis.com/auth/gmail.readonly"
GMAIL_QUERY = "(from:steampowered.com OR from:steam-support.com) newer_than:1d"
GMAIL_HOST_FILTER = "steam"
# Сколько секунд назад должно прийти письмо, чтобы его взяли (для подтверждения)
MAIL_MAX_AGE = 15
# Сколько ждать письмо с подтверждением, прежде чем перезапустить Chrome
CONFIRM_MAIL_TIMEOUT = 7
# Сколько раз перезапускать браузер, пока письмо так и не пришло
CONFIRM_MAIL_RETRIES = 3

URL_RE = re.compile(r"https?://[^\s\"'<>\])\]]+")
STEAMID64_RE = re.compile(r"/profiles/(\d{17})")
STEAM_CODE_RE = re.compile(r"\b([A-Z0-9]{5})\b")

DEFAULT_SETTINGS = {
    "headless": "true",
    "account_total": "1",
    "account_gap": "1",
    "nonecap_api_key": "",
    "discord_webhook": "",
    "custom_name": "",
    "avatar": "true",
    "colors": "true",
    "proxy_enabled": "false",
    "proxy": "",
}

NONECAP_API_KEY = ""
DISCORD_WEBHOOK = ""
CUSTOM_NAME = ""
AVATAR_ENABLED = True

# ==== PROXY ====
# Можно писать как угодно: 1.2.3.4:8000, http://1.2.3.4:8000,
# socks5://user:pass@1.2.3.4:1080, https://..., socks4://...
# Несколько прокси через запятую / точку с запятой / перенос строки = случайный выбор на аккаунт.
PROXY_ENABLED = False
PROXY_VALUE = ""
PROXY_SCHEMES = {
    "http": "http",
    "https": "https",
    "socks4": "socks4",
    "socks4a": "socks4",
    "socks5": "socks5",
    "socks5h": "socks5",
}
PROXY_RE = re.compile(
    r"^(?:(?P<scheme>[A-Za-z][A-Za-z0-9+.\-]*)://)?"
    r"(?:(?P<user>[^:@/\s]+):(?P<password>[^@/\s]*)@)?"
    r"(?P<host>[^:@/\s]+)"
    r":(?P<port>\d{1,5})$"
)


def cleanup_pycache():
    cache_dir = BASE_DIR / "__pycache__"
    if not cache_dir.is_dir():
        return
    for pyc in cache_dir.glob(f"{MODULE_NAME}*.pyc"):
        try:
            pyc.unlink()
        except OSError:
            pass
    try:
        next(cache_dir.iterdir())
    except StopIteration:
        try:
            cache_dir.rmdir()
        except OSError:
            pass
    except OSError:
        pass


atexit.register(cleanup_pycache)

# ==== ДИЗАЙН (1:1 как в C++ проекте) ====
# Градиент подписей меню
GRADIENT_START = (140, 120, 255)
GRADIENT_END = (80, 200, 255)
# Вертикальный градиент баннера
BANNER_GRADIENT_START = (100, 60, 220)
BANNER_GRADIENT_END = (60, 180, 255)
# Цвета уровней логов
LOG_INFO = (140, 120, 255)
LOG_SUCCESS = (80, 230, 120)
LOG_WARNING = (255, 200, 60)
LOG_ERROR = (255, 100, 100)
# Символы уровней
LOG_SYMBOLS = {"info": "*", "success": "+", "warning": "!", "error": "x"}
# Остальные цвета
COLOR_DIM = (60, 65, 80)
COLOR_MUTED = (90, 95, 110)
COLOR_LABEL = (80, 85, 100)
COLOR_VALUE = (140, 170, 200)
COLOR_TITLE = (140, 120, 255)
COLOR_SUCCESS = LOG_SUCCESS
COLOR_ERROR = LOG_ERROR
COLOR_WARN = LOG_WARNING
COLOR_TEXT = (205, 210, 225)
COLOR_BUTTON = (95, 175, 230)
# Фон бейджей
BADGE_BG_SUCCESS = (80, 230, 120)
BADGE_BG_ERROR = (255, 70, 70)
BADGE_FG = (30, 30, 35)
# Размер консоли
CONSOLE_WIDTH = 123
CONSOLE_HEIGHT = 30
# Заголовок окна
APP_TITLE = "SteamAccGen v1.0"
# Текст между линиями-разделителями под баннером
BANNER_DIVIDER_TEXT = " SteamAccGen "
# Отступ меню и инфо о ПК справа
MENU_INFO_OFFSET = 44

# Символы рамок
BOX_TL, BOX_TR, BOX_BL, BOX_BR = "\u256d", "\u256e", "\u2570", "\u256f"
BOX_H, BOX_V = "\u2500", "\u2502"

COLORS_ENABLED_SETTING = True
COLOR_ENABLED = False


def _supports_color():
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("WT_SESSION") or os.environ.get("TERM_PROGRAM"):
        return True
    return os.name == "nt" and sys.stdout.isatty()


def resolve_color_enabled():
    global COLOR_ENABLED
    COLOR_ENABLED = COLORS_ENABLED_SETTING and _supports_color()
    return COLOR_ENABLED


RESET = "\x1b[0m"
BOLD = "\x1b[1m"


def _rgb(r, g, b):
    return f"\x1b[38;2;{r};{g};{b}m"


def _bg_rgb(r, g, b):
    return f"\x1b[48;2;{r};{g};{b}m"


def color(text, rgb_color, bold=False):
    """Оборачивает текст в цвет. Возвращает как есть, если цвета выключены."""
    if not COLOR_ENABLED:
        return text
    prefix = BOLD if bold else ""
    return f"{prefix}{_rgb(*rgb_color)}{text}{RESET}"


def lerp_rgb(t, start, end):
    """Линейная интерполяция цвета — как LerpRgb в C++ версии."""
    t = max(0.0, min(1.0, t))
    return (
        int(start[0] + (end[0] - start[0]) * t),
        int(start[1] + (end[1] - start[1]) * t),
        int(start[2] + (end[2] - start[2]) * t),
    )


def gradient_text(text, start=GRADIENT_START, end=GRADIENT_END):
    """Посимвольный градиент по всей строке."""
    if not COLOR_ENABLED or len(text) < 2:
        return color(text, start)
    result = []
    n = len(text) - 1
    for i, ch in enumerate(text):
        r, g, b = lerp_rgb(i / n, start, end)
        result.append(_rgb(r, g, b) + ch)
    return "".join(result) + RESET


def write(text):
    sys.stdout.write(text)
    sys.stdout.flush()


def say(text=""):
    print(gradient_text(text))


def ask(prompt):
    return input(gradient_text(prompt))


def prompt_line(label):
    """Приглашение к вводу с отступом 2 пробела — как PromptLine в C++."""
    try:
        return input("  " + label)
    except (EOFError, KeyboardInterrupt):
        raise


LOG_LEVELS = {
    "info": ("*", LOG_INFO),
    "success": ("+", LOG_SUCCESS),
    "warning": ("!", LOG_WARNING),
    "error": ("x", LOG_ERROR),
}

_RGB_TO_LEVEL = {
    LOG_INFO: "info",
    LOG_SUCCESS: "success",
    LOG_WARNING: "warning",
    LOG_ERROR: "error",
    GRADIENT_START: "info",
}


_UI_QUIET = {"on": False}
_SCAN_ABORT = {"stop": False}


def set_quiet(on):
    """Тихий режим: логи и print_box молчат, чтобы не сыпать инфу во время парсинга."""
    _UI_QUIET["on"] = bool(on)


def ui_quiet():
    return _UI_QUIET["on"]


def reset_abort():
    _SCAN_ABORT["stop"] = False


def scan_stopped():
    return _SCAN_ABORT["stop"]


def enter_pressed():
    """True, если пользователь нажал Enter. Не блокирует."""
    if os.name != "nt":
        return False
    try:
        import msvcrt
        while msvcrt.kbhit():
            if msvcrt.getwch() in ("\r", "\n"):
                _SCAN_ABORT["stop"] = True
                return True
    except Exception:
        pass
    return False


def check_abort():
    """Проверяет Enter и пишет подсказку один раз."""
    if enter_pressed():
        if not _SCAN_ABORT.get("hinted"):
            log("Останавливаюсь — Enter нажат. Сохраню что успел найти.", "warning")
            _SCAN_ABORT["hinted"] = True
        return True
    return False


def log(text, level="info"):
    """
    Строка лога в стиле C++ версии:
        12:34:56 [+] сообщение
    Время — тёмное, символ уровня — цветной, текст — обычным.
    """
    if _UI_QUIET["on"]:
        return
    symbol, level_rgb = LOG_LEVELS.get(level, LOG_LEVELS["info"])
    stamp = datetime.now().strftime("%H:%M:%S")
    if not COLOR_ENABLED:
        print(f"{stamp} [{symbol}] {text}")
        return
    write(_rgb(*COLOR_DIM) + stamp + RESET)
    write(_rgb(*level_rgb) + f"[{symbol}]" + RESET)
    write(" " + str(text) + "\n")


def _nearest_level(rgb_color):
    """Подбирает уровень лога, ближайший к переданному цвету."""
    if not rgb_color:
        return "info"
    rgb_color = tuple(rgb_color)
    if rgb_color in _RGB_TO_LEVEL:
        return _RGB_TO_LEVEL[rgb_color]
    best, best_dist = "info", None
    for name, (_symbol, ref) in LOG_LEVELS.items():
        dist = sum((a - b) ** 2 for a, b in zip(rgb_color, ref))
        if best_dist is None or dist < best_dist:
            best, best_dist = name, dist
    return best


def log_line(text, rgb_color=None, bold=False):
    """
    Совместимая обёртка: старые вызовы передают RGB-цвет.
    Цвет автоматически превращается в уровень лога.
    """
    if _UI_QUIET["on"]:
        return
    log(str(text), _nearest_level(rgb_color))


def print_result(success, message, detail=None):
    """Бейдж SUCCESS / FAIL с фоновым цветом — как PrintResult в C++."""
    if success:
        badge, message_rgb, bg = " SUCCESS ", LOG_SUCCESS, BADGE_BG_SUCCESS
    else:
        badge, message_rgb, bg = "  FAIL   ", LOG_ERROR, BADGE_BG_ERROR

    write("\n  ")
    if COLOR_ENABLED:
        write(_bg_rgb(*bg) + _rgb(*BADGE_FG) + badge + RESET)
        write(" " + _rgb(*message_rgb) + str(message) + RESET)
    else:
        write(f"{badge} {message}")
    write("\n")

    if detail:
        write("  " + color(detail, COLOR_MUTED) + "\n")


def print_box(label, value, value_rgb=COLOR_VALUE):
    """Строка вида '  Метка       Значение' — как PrintBox в C++."""
    if _UI_QUIET["on"]:
        return
    text = truncate_plain(str(value), CONSOLE_WIDTH - 16)
    key = truncate_plain(str(label), 40)
    # Короткая метка паддится до 12 колонок, длинная — отделяется пробелами
    gap = "  " if display_width(key) >= 12 else ""
    write("  " + color(key.ljust(12), COLOR_LABEL) + gap + color(text, value_rgb) + "\n")


def print_rule(text="", rgb=COLOR_DIM, width=None, indent="  "):
    """Горизонтальная линия, опционально с текстом по центру."""
    width = width or CONSOLE_WIDTH - 4
    if not text:
        write(indent + color(BOX_H * width, rgb) + "\n")
        return
    body = truncate_plain(text, max(0, width - 4))
    left = max(0, (width - display_width(body)) // 2)
    right = max(0, width - display_width(body) - left)
    write(indent + color(BOX_H * left + " " + body + " " + BOX_H * right, rgb) + "\n")


def get_timestamp():
    return datetime.now().strftime("%H:%M:%S")


def get_date_string():
    return datetime.now().strftime("%d.%m.%y %H:%M:%S")


BANNER = [
    ' ███▄    █  ██▓  ▄████   ▄████  ▄▄▄           ▄████ ▓█████  ███▄    █ ▓█████  ██▀███   ▄▄▄     ▄▄▄█████▓ ▒█████   ██▀███  "',
    ' ██ ▀█   █ ▓██▒ ██▒ ▀█▒ ██▒ ▀█▒▒████▄        ██▒ ▀█▒▓█   ▀  ██ ▀█   █ ▓█   ▀ ▓██ ▒ ██▒▒████▄   ▓  ██▒ ▓▒▒██▒  ██▒▓██ ▒ ██▒"',
    '▓██  ▀█ ██▒▒██▒▒██░▄▄▄░▒██░▄▄▄░▒██  ▀█▄     ▒██░▄▄▄░▒███   ▓██  ▀█ ██▒▒███   ▓██ ░▄█ ▒▒██  ▀█▄ ▒ ▓██░ ▒░▒██░  ██▒▓██ ░▄█ ▒"',
    '▓██▒  ▐▌██▒░██░░▓█  ██▓░▓█  ██▓░██▄▄▄▄██    ░▓█  ██▓▒▓█  ▄ ▓██▒  ▐▌██▒▒▓█  ▄ ▒██▀▀█▄  ░██▄▄▄▄██░ ▓██▓ ░ ▒██   ██░▒██▀▀█▄ "',
    '▒██░   ▓██░░██░░▒▓███▀▒░▒▓███▀▒ ▓█   ▓██▒   ░▒▓███▀▒░▒████▒▒██░   ▓██░░▒████▒░██▓ ▒██▒ ▓█   ▓██▒ ▒██▒ ░ ░ ████▓▒░░██▓ ▒██▒"',
    '░ ▒░   ▒ ▒ ░▓   ░▒   ▒  ░▒   ▒  ▒▒   ▓▒█░    ░▒   ▒ ░░ ▒░ ░░ ▒░   ▒ ▒ ░░ ▒░ ░░ ▒▓ ░▒▓░ ▒▒   ▓▒█░ ▒ ░░   ░ ▒░▒░▒░ ░ ▒▓ ░▒▓░"',
    '░ ░░   ░ ▒░ ▒ ░  ░   ░   ░   ░   ▒   ▒▒ ░     ░   ░  ░ ░  ░░ ░░   ░ ▒░ ░ ░  ░  ░▒ ░ ▒░  ▒   ▒▒ ░   ░      ░ ▒ ▒░   ░▒ ░ ▒░"',
    '   ░   ░ ░  ▒ ░░ ░   ░ ░ ░   ░   ░   ▒      ░ ░   ░    ░      ░   ░ ░    ░     ░░   ░   ░   ▒    ░      ░ ░ ░ ▒    ░░   ░ "',
    '         ░  ░        ░       ░       ░  ░         ░    ░  ░         ░    ░  ░   ░           ░  ░            ░ ░     ░      "',
    '                                                                                                                           "',
]

CONSOLE_FONTS = [
    "Cascadia Mono",
    "Cascadia Code",
    "Consolas",
    "Lucida Console",
    "DejaVu Sans Mono",
]


class COORD(ctypes.Structure):
    _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]


class SMALL_RECT(ctypes.Structure):
    _fields_ = [("Left", ctypes.c_short), ("Top", ctypes.c_short),
                ("Right", ctypes.c_short), ("Bottom", ctypes.c_short)]


class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
    _fields_ = [("dwSize", COORD), ("dwCursorPosition", COORD),
                ("wAttributes", ctypes.c_ushort),
                ("srWindow", SMALL_RECT),
                ("dwMaximumWindowSize", COORD)]


class CONSOLE_FONT_INFOEX(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_ulong),
        ("dwFontSize", ctypes.c_short * 2),
        ("FontWeight", ctypes.c_ushort),
        ("FontFamily", ctypes.c_ushort),
        ("FontPitchAndFamily", ctypes.c_uint),
        ("FaceName", ctypes.c_wchar * 32),
    ]


def set_console_font(face="Cascadia Code", height=16):
    """Отключено: приложение не подменяет шрифт консоли."""
    return False


ORIGINAL_CONSOLE_FONT = None


def capture_console_font():
    """Запоминает шрифт, с которым консоль запущена."""
    global ORIGINAL_CONSOLE_FONT
    if os.name != "nt":
        return
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        info = CONSOLE_FONT_INFOEX()
        info.cbSize = ctypes.sizeof(CONSOLE_FONT_INFOEX)
        if kernel32.GetCurrentConsoleFontEx(handle, False, ctypes.byref(info)):
            ORIGINAL_CONSOLE_FONT = info
    except Exception:
        ORIGINAL_CONSOLE_FONT = None


def restore_console_font():
    """Возвращает шрифт, который был до запуска программы."""
    if os.name != "nt" or ORIGINAL_CONSOLE_FONT is None:
        return False
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        return bool(kernel32.SetCurrentConsoleFontEx(handle, False,
                                                     ctypes.byref(ORIGINAL_CONSOLE_FONT)))
    except Exception:
        return False


def set_console_title(title=APP_TITLE):
    if os.name != "nt":
        return
    try:
        ctypes.windll.kernel32.SetConsoleTitleW(title)
    except Exception:
        pass


def resize_console(width=CONSOLE_WIDTH, height=CONSOLE_HEIGHT):
    """Меняет размер буфера и окна консоли — как ResizeConsole в C++."""
    if os.name != "nt":
        return False
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        buf = COORD(width, height)
        kernel32.SetConsoleScreenBufferSize(handle, buf)

        win = SMALL_RECT(0, 0, width - 1, height - 1)
        kernel32.SetConsoleWindowInfo(handle, True, ctypes.byref(win))
        return True
    except Exception:
        return False


def hide_cursor():
    write("\x1b[?25l")


def show_cursor():
    write("\x1b[?25h")


def enable_unicode_output():
    if os.name == 'nt':
        set_console_title()
        os.system('chcp 65001 >nul')
        try:
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)
            mode = ctypes.c_ulong()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                kernel32.SetConsoleMode(handle, mode.value | 0x4)
        except Exception:
            pass
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass


def print_banner():
    """Баннер с вертикальным градиентом + разделитель с названием."""
    write("\n")
    total = len(BANNER)
    for i, line in enumerate(BANNER):
        r, g, b = lerp_rgb(i / (total - 1) if total > 1 else 0.0,
                           BANNER_GRADIENT_START, BANNER_GRADIENT_END)
        write(_rgb(r, g, b) + line + "\n")
    write(RESET)
    write("\n  ")
    write(_rgb(*COLOR_DIM) + BOX_H * 16)
    write(_rgb(*COLOR_TITLE) + BOLD + BANNER_DIVIDER_TEXT + RESET)
    write(_rgb(*COLOR_DIM) + BOX_H * 16 + RESET)
    write("\n\n")


def print_menu_item(number, label, indent=""):
    """Пункт меню: [N] в фиолетовом + название с градиентом."""
    write(indent)
    write(color(f"[{number}] ", COLOR_TITLE))
    write(gradient_text(label) + "\n")


def pc_info_lines():
    return [
        "PC Information:",
        f"Computer: {os.environ.get('COMPUTERNAME', 'unknown')}",
        f"User: {os.environ.get('USERNAME', 'unknown')}",
    ]


def print_main_menu():
    """Главное меню + инфо о ПК справа (колонка 44) — как PrintMainMenu в C++."""
    items = ["Generate", "Setting", "Inbox", "Exit"]
    info = pc_info_lines()

    for i, label in enumerate(items):
        write(color(f"[{i + 1}] ", COLOR_TITLE))
        write(gradient_text(label))

        # Справа — инфо о ПК, только для первых трёх пунктов
        if i < 3 and i < len(info):
            used = len(label) + 4
            write(" " * max(1, MENU_INFO_OFFSET - used))
            write(color(info[i], COLOR_DIM) + "\n")
        else:
            write("\n")


def clear_screen():
    """Полная очистка буфера консоли с переносом курсора в 0,0."""
    if os.name == 'nt':
        try:
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)

            csbi = CONSOLE_SCREEN_BUFFER_INFO()
            if not kernel32.GetConsoleScreenBufferInfo(handle, ctypes.byref(csbi)):
                raise OSError("no console")

            cells = csbi.dwSize.X * csbi.dwSize.Y
            written = ctypes.c_ulong()
            origin = COORD(0, 0)

            fill_char = ctypes.c_wchar(" ")
            kernel32.FillConsoleOutputCharacterW(handle, fill_char, cells,
                                                 origin, ctypes.byref(written))
            kernel32.FillConsoleOutputAttribute(handle, csbi.wAttributes, cells,
                                                origin, ctypes.byref(written))
            kernel32.SetConsoleCursorPosition(handle, origin)
            return
        except Exception:
            pass
    os.system('cls' if os.name == 'nt' else 'clear')


def truncate_plain(text, width):
    if text is None:
        return ""
    if display_width(text) <= width:
        return text
    if width <= 3:
        return text[:width]
    trimmed = text
    while trimmed and display_width(trimmed) > width - 3:
        trimmed = trimmed[:-1]
    return trimmed.rstrip() + "..."


def display_width(text):
    total = 0
    for ch in text or "":
        code = ord(ch)
        wide = (
            0x1100 <= code <= 0x115F
            or 0x2E80 <= code <= 0xA4CF
            or 0xAC00 <= code <= 0xD7A3
            or 0xF900 <= code <= 0xFAFF
            or 0xFE30 <= code <= 0xFE6F
            or 0xFF00 <= code <= 0xFF60
            or 0xFFE0 <= code <= 0xFFE6
        )
        total += 2 if wide else 1
    return total


# ==========================================================================
#          INBOX
# ==========================================================================

IB_WIDTH = CONSOLE_WIDTH - 4
IB_PANEL_WIDTH = IB_WIDTH
IB_INNER_WIDTH = IB_WIDTH
IB_PANEL_INDENT = "  "

IB_ACCENT = (255, 210, 90)
IB_TIME = (120, 200, 255)
IB_SUBJECT = (235, 225, 255)

IB_DOT = "\u25cf"
IB_SPINNER = ("\u280b", "\u2819", "\u2839", "\u2838", "\u283c",
              "\u2834", "\u2826", "\u2827", "\u2807", "\u280f")

INBOX_POLL_INTERVAL = 2
INBOX_RECENT_MINUTES = 30
INBOX_RECENT_LIMIT = 30

_IB_LIVE = {"active": False, "width": 0}
_IB_COMPACT = False

IB_GLYPHS = {
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
}


def ib_rule(*args, rgb=None, width=None, fill=None):
    """Линия-разделитель в том же стиле, что и остальной интерфейс."""
    text = None
    for arg in args:
        if isinstance(arg, str):
            text = arg
        elif isinstance(arg, tuple):
            rgb = arg
    symbol = fill or BOX_H
    width = width or IB_WIDTH
    rgb = rgb or COLOR_DIM

    if not text:
        write(IB_PANEL_INDENT + color(symbol * width, rgb) + "\n")
        return

    body = truncate_plain(text, max(0, width - 4))
    slack = max(0, width - display_width(body) - 2)
    left = slack // 2
    right = slack - left
    write(IB_PANEL_INDENT
          + color(symbol * left + " " + body + " " + symbol * right, rgb) + "\n")


def ib_glyph_rows(ch):
    pattern = IB_GLYPHS.get(ch.upper())
    if not pattern:
        return []
    return ["".join("\u2588" if cell == "1" else "\u2591" for cell in row)
            for row in pattern]


def ib_big_text(text, gap=2, rgb=COLOR_SUCCESS):
    """Крупный код 5x7 — по центру рабочей области, без рамки."""
    rows = [""] * 7
    for index, ch in enumerate(text):
        glyph = ib_glyph_rows(ch)
        if not glyph:
            continue
        for i in range(7):
            rows[i] += glyph[i]
        if gap and index != len(text) - 1:
            for i in range(7):
                rows[i] += " " * gap

    painted = []
    for row in rows:
        pad = " " * max(0, (IB_WIDTH - display_width(row)) // 2)
        right = " " * max(0, IB_WIDTH - display_width(row) - len(pad))
        painted.append(IB_PANEL_INDENT + pad + color(row, rgb, True) + right)
    return painted


def ib_term_width():
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return CONSOLE_WIDTH


def ib_live_status(text, rgb=COLOR_DIM, frame=" ", highlight=False):
    if _IB_COMPACT:
        return
    body = f" {frame} {text}"
    body = truncate_plain(body, max(20, ib_term_width() - 2))
    pad = " " * max(0, _IB_LIVE["width"] - len(body))
    _IB_LIVE["width"] = len(body)
    _IB_LIVE["active"] = True
    sys.stdout.write("\r" + (color(body, rgb, highlight) if COLOR_ENABLED else body) + pad)
    sys.stdout.flush()


def ib_clear_live_status():
    if not _IB_LIVE["active"]:
        return
    sys.stdout.write("\r" + " " * _IB_LIVE["width"] + "\r")
    sys.stdout.flush()
    _IB_LIVE["active"] = False
    _IB_LIVE["width"] = 0


def ib_log(text, rgb=COLOR_TEXT, bold=False, icon=None):
    """Лог инбокса — формат тот же, что у основного log()."""
    ib_clear_live_status()
    log(str(text), _nearest_level(rgb))


IB_CODE_BLACKLIST = {
    "STEAM", "HTTPS", "LOGIN", "EMAIL", "TODAY",
    "ABOUT", "AFTER", "AGAIN", "COULD", "EVERY", "FIRST",
    "FOUND", "GREAT", "HOUSE", "LARGE", "LATER", "LEARN",
    "NEVER", "OTHER", "PLACE", "POINT", "RIGHT", "SMALL",
    "SOUND", "SPELL", "STILL", "STUDY", "THEIR", "THERE",
    "THESE", "THING", "THINK", "THREE", "UNDER", "WATER",
    "WHERE", "WHICH", "WHILE", "WHITE", "WHOLE", "WOMAN",
    "WOULD", "WRITE", "YOUNG", "HTTP", "HTML", "WWW", "COM",
    "NET", "ORG", "GMAIL", "VALVE", "ACCOUNT", "SECURITY",
    "TERMS", "PRIVACY", "COOKIE", "HELP",
}


def ib_valid_code(code):
    if not code or len(code) != 5 or not code.isalnum():
        return False
    return code.upper() not in IB_CODE_BLACKLIST


def ib_extract_code(mail):
    text = mail.get("text") or ""
    html = mail.get("html") or ""
    patterns = [
        r"(?:\u043a\u043e\u0434|code)[:\s]+([A-Z0-9]{5})\b",
        r"(?:\u0432\u0430\u0448\s+\u043a\u043e\u0434|your\s+code)[:\s]+([A-Z0-9]{5})\b",
        r"([A-Z0-9]{5})\s*(?:\u2014|\u2013|\u044d\u0442\u043e \u0432\u0430\u0448 \u043a\u043e\u0434|is your code)",
        r"Steam Guard[^\n]{0,40}?([A-Z0-9]{5})\b",
    ]
    for src in (text, html):
        if not src:
            continue
        plain = src
        if "<" in plain:
            plain = re.sub(r"<[^>]+>", " ", plain)
            plain = re.sub(r"&nbsp;", " ", plain)
            plain = re.sub(r"&amp;", "&", plain)
        for pattern in patterns:
            match = re.search(pattern, plain, re.IGNORECASE)
            if match:
                code = match.group(1).upper()
                if ib_valid_code(code):
                    return code

    for src in (text, html):
        if not src:
            continue
        plain = re.sub(r"<[^>]+>", " ", src) if "<" in src else src
        for code in STEAM_CODE_RE.findall(plain):
            if ib_valid_code(code):
                return code.upper()
    return None


def ib_clean_preview(text, max_len=190):
    if not text:
        return ""
    plain = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    plain = re.sub(r"<script[^>]*>.*?</script>", " ", plain, flags=re.DOTALL | re.IGNORECASE)
    plain = re.sub(r"<[^>]+>", " ", plain)
    plain = re.sub(r"&nbsp;", " ", plain)
    plain = re.sub(r"&amp;", "&", plain)
    plain = re.sub(r"&quot;", '"', plain)
    plain = re.sub(r"&#\d+;", " ", plain)
    plain = re.sub(r"\s+", " ", plain).strip()
    if len(plain) > max_len:
        plain = plain[:max_len].rstrip() + "..."
    return plain


def ib_mail_time(mail):
    if mail.get("internal_ms"):
        return datetime.fromtimestamp(mail["internal_ms"] / 1000)
    if mail.get("date_dt"):
        dt = mail["date_dt"]
        return dt.astimezone().replace(tzinfo=None) if dt.tzinfo else dt
    return None


def ib_sort_key(mail):
    if mail.get("internal_ms"):
        return mail["internal_ms"]
    if mail.get("date_dt"):
        return int(mail["date_dt"].timestamp() * 1000)
    return 0


def ib_mail_card(mail, index=None, title="NEW MAIL", accent=COLOR_SUCCESS, compact=False):
    when = ib_mail_time(mail)
    time_str = when.strftime("%H:%M:%S") if when else "??:??:??"
    date_str = when.strftime("%d.%m.%Y") if when else ""
    subject = (mail.get("subject") or "\u0431\u0435\u0437 \u0442\u0435\u043c\u044b").strip()
    sender = (mail.get("from") or "\u043d\u0435\u0438\u0437\u0432\u0435\u0441\u0442\u043d\u043e").strip()
    code = ib_extract_code(mail)
    preview = ib_clean_preview(mail.get("text") or mail.get("html") or "")

    header = f"{IB_DOT} {title}"
    if index is not None:
        header += f" #{index}"
    header += f"   {time_str}"

    write("\n")
    ib_rule(header, rgb=accent)

    if code and not compact:
        for row in ib_big_text(code, rgb=accent):
            write(row + "\n")
        ib_rule()
    elif code:
        print_box("CODE", code, accent)

    print_box("Subject", subject, IB_SUBJECT)
    print_box("From", sender, COLOR_DIM)
    print_box("Date", f"{date_str} {time_str}".strip(), COLOR_DIM)

    if not code:
        print_box("Warning", "Steam Guard code not found in this mail", LOG_WARNING)

    if preview:
        words, wrapped, current = preview.split(), [], ""
        for word in words:
            if len(current) + len(word) + 1 > 64:
                wrapped.append(current)
                current = word
            else:
                current = f"{current} {word}".strip()
        if current:
            wrapped.append(current)
        for chunk in wrapped[:4]:
            print_box("Preview", chunk, COLOR_DIM)

    write("\n")


def ib_profile_email():
    try:
        access = _gmail_access_token()
        response = requests.get(f"{GMAIL_API}/profile",
                                headers={"Authorization": "Bearer " + access},
                                timeout=20)
        if response.status_code == 200:
            return response.json().get("emailAddress", "")
    except Exception:
        pass
    return ""


def ib_show_header(email, interval, compact):
    clear_screen()
    print_banner()

    write("  " + color("INBOX MONITOR", GRADIENT_START, bold=True) + "\n")
    ib_rule()
    print_box("Account", email or "connecting to Gmail...", COLOR_TEXT)
    print_box("Interval", f"every {interval}s", COLOR_DIM)
    print_box("Code view", "compact" if compact else "large 5x7 font", COLOR_DIM)
    print_box("Source", "Gmail API \u2022 scope gmail.readonly", COLOR_DIM)
    print_box("Filter", GMAIL_QUERY, COLOR_DIM)
    ib_rule()
    write("  " + color("[r] refresh   [b] code view   [i] interval   "
                       "[c] clear   [q] back to menu", COLOR_DIM) + "\n")
    write("\n")


def ib_show_recent_mails(minutes=INBOX_RECENT_MINUTES, limit=INBOX_RECENT_LIMIT, compact=False):
    try:
        mails = gmail_inbox_mails(limit=limit, query="from:steampowered.com")
    except Exception as e:
        ib_log(f"\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u043f\u043e\u043b\u0443\u0447\u0438\u0442\u044c "
               f"\u043f\u0438\u0441\u044c\u043c\u0430: {e}", COLOR_ERROR, icon="\u2717")
        return []

    if not mails:
        ib_log("\u041f\u0438\u0441\u0435\u043c \u043e\u0442 Steam \u0432 \u044f\u0449\u0438\u043a\u0435 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u043e",
               COLOR_WARN, icon="\u26a0")
        return []

    cutoff_ms = int((time.time() - minutes * 60) * 1000)
    now = datetime.now()
    recent = []
    for mail in mails:
        if mail.get("internal_ms"):
            if mail["internal_ms"] >= cutoff_ms:
                recent.append(mail)
        elif mail.get("date_dt"):
            dt = mail["date_dt"]
            dt_cmp = dt.astimezone().replace(tzinfo=None) if dt.tzinfo else dt
            if (now - dt_cmp).total_seconds() <= minutes * 60:
                recent.append(mail)

    ib_rule(f" \u25bc STEAM MAILS, LAST {minutes} MIN ")

    if not recent:
        ib_log(f"\u0417\u0430 \u043f\u043e\u0441\u043b\u0435\u0434\u043d\u0438\u0435 {minutes} \u043c\u0438\u043d "
               f"\u043f\u0438\u0441\u0435\u043c \u043d\u0435\u0442 (\u0432\u0441\u0435\u0433\u043e \u0437\u0430 "
               f"\u0441\u0443\u0442\u043a\u0438: {len(mails)})", COLOR_WARN, icon="\u26a0")
        print()
        return []

    recent.sort(key=ib_sort_key, reverse=True)
    ib_log(f"\u041d\u0430\u0439\u0434\u0435\u043d\u043e \u043f\u0438\u0441\u0435\u043c: {len(recent)}",
           COLOR_SUCCESS, bold=True, icon="\u2713")

    codes = []
    for index, mail in enumerate(recent, 1):
        code = ib_extract_code(mail)
        if code:
            codes.append(code)
        if index <= 3:
            ib_mail_card(mail, index=index, title="RECENT MAIL",
                         accent=IB_ACCENT, compact=compact)
        else:
            when = ib_mail_time(mail)
            time_str = when.strftime("%d.%m %H:%M:%S") if when else "??"
            subject = truncate_plain((mail.get("subject") or "(\u0431\u0435\u0437 \u0442\u0435\u043c\u044b)").strip(), 40)
            tail = color(code, COLOR_SUCCESS, True) if code else color("--------", COLOR_DIM)
            write(IB_PANEL_INDENT + color(f"{time_str:<15}", IB_TIME)
                  + color(truncate_plain(subject, 70), IB_SUBJECT)
                  + "  " + tail + "\n")

    write("\n")
    if codes:
        print_box("\u041a\u043e\u0434\u044b", "  ".join(codes), COLOR_SUCCESS)
    else:
        print_box("\u041a\u043e\u0434\u044b", "Steam Guard codes not found in these mails",
                  LOG_WARNING)
    write("\n")
    return recent


def ib_handle_key(ch, state):
    key = (ch or "").lower()
    if key == "q":
        ib_log("\u0412\u043e\u0437\u0432\u0440\u0430\u0442 \u0432 \u0433\u043b\u0430\u0432\u043d\u043e\u0435 \u043c\u0435\u043d\u044e",
               COLOR_WARN, icon="\u25a0")
        state["quit"].set()
        return
    if key == "r":
        state["refresh"].set()
        ib_live_status("\u043e\u0431\u043d\u043e\u0432\u043b\u044f\u044e Gmail...", IB_ACCENT,
                       frame=IB_SPINNER[int(time.time() * 10) % len(IB_SPINNER)], highlight=True)
        return
    if key == "b":
        state["compact"] = not state["compact"]
        kind = "\u043a\u043e\u043c\u043f\u0430\u043a\u0442\u043d\u044b\u0439" if state["compact"] else "\u043a\u0440\u0443\u043f\u043d\u044b\u0439"
        ib_log(f"\u0412\u0438\u0434 \u043a\u043e\u0434\u0430: {kind}", COLOR_SUCCESS, icon="\u2713")
        return
    if key == "c":
        ib_show_header(state.get("email", ""), state["interval"], state["compact"])
        return
    if key == "i":
        ib_clear_live_status()
        try:
            value = input("  " + color("Enter new interval in seconds (1-60): ",
                                        IB_ACCENT))
        except (EOFError, KeyboardInterrupt):
            return
        value = value.strip()
        if value.isdigit() and 1 <= int(value) <= 60:
            state["interval"] = int(value)
            ib_log(f"\u0418\u043d\u0442\u0435\u0440\u0432\u0430\u043b: {state['interval']} \u0441\u0435\u043a",
                   COLOR_SUCCESS, icon="\u2713")
        else:
            ib_log("\u041d\u0443\u0436\u043d\u043e \u0447\u0438\u0441\u043b\u043e \u043e\u0442 1 \u0434\u043e 60",
                   COLOR_ERROR, icon="\u2717")
        time.sleep(1.0)


def ib_key_listener(state):
    try:
        import msvcrt
    except ImportError:
        return
    while not state["quit"].is_set():
        try:
            if msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch in ("\x00", "\xe0"):
                    msvcrt.getwch()
                    continue
                if ch in ("\r", "\n"):
                    continue
                if ch == "\x03":
                    state["quit"].set()
                    return
                ib_handle_key(ch, state)
            else:
                time.sleep(0.05)
        except Exception:
            return


def inbox_watch_loop():
    global _IB_COMPACT
    ib_clear_live_status()
    set_console_title("SteamAccGen \u2022 Inbox Monitor")

    state = {
        "quit": threading.Event(),
        "refresh": threading.Event(),
        "compact": False,
        "interval": INBOX_POLL_INTERVAL,
        "email": "",
    }

    ib_show_header("", state["interval"], state["compact"])
    ib_log("\u041f\u043e\u0434\u043a\u043b\u044e\u0447\u0430\u044e\u0441\u044c \u043a Gmail...",
           COLOR_WARN, icon="\u21bb")

    def _load_email():
        found = ib_profile_email()
        if found and not state["quit"].is_set():
            state["email"] = found
            ib_log(f"\u042f\u0449\u0438\u043a: {found}", COLOR_SUCCESS, bold=True, icon="\u2713")
            ib_show_header(found, state["interval"], state["compact"])

    authorizer = threading.Thread(target=_load_email, daemon=True)
    authorizer.start()
    authorizer.join(timeout=300)

    ib_show_recent_mails(minutes=INBOX_RECENT_MINUTES, limit=INBOX_RECENT_LIMIT,
                         compact=state["compact"])
    ib_rule(" \u25b6 INBOX ACTIVE ")
    ib_log("\u0421\u043b\u0435\u0436\u0443 \u0437\u0430 \u043d\u043e\u0432\u044b\u043c\u0438 \u043f\u0438\u0441\u044c\u043c\u0430\u043c\u0438 "
           "Steam. [q] \u2014 \u0432\u044b\u0445\u043e\u0434 \u0432 \u043c\u0435\u043d\u044e.", COLOR_DIM)

    seen_ids = set()
    seen_codes = set()
    first_check = True
    new_mails = 0
    new_codes = 0
    scans = 0
    last_error = ""
    started = time.time()
    threading.Thread(target=ib_key_listener, args=(state,), daemon=True).start()

    while not state["quit"].is_set():
        loop_start = time.time()
        state["refresh"].clear()
        interval = state["interval"]
        _IB_COMPACT = state["compact"]

        try:
            mails = gmail_inbox_mails(limit=8)
            last_error = ""
        except Exception as e:
            last_error = str(e)
            ib_log(f"Gmail error: {truncate_plain(last_error, 80)}", COLOR_ERROR, icon="\u2717")
            mails = []

        scans += 1
        fresh = [mail for mail in mails if mail["id"] not in seen_ids]
        for mail in mails:
            seen_ids.add(mail["id"])

        if first_check:
            for mail in fresh:
                code = ib_extract_code(mail)
                if code:
                    seen_codes.add(code)
            first_check = False
            if not fresh:
                ib_log("Gmail \u043f\u043e\u0434\u043a\u043b\u044e\u0447\u0451\u043d, \u043d\u043e\u0432\u044b\u0445 "
                       "\u043f\u0438\u0441\u0435\u043c \u043d\u0435\u0442", COLOR_SUCCESS, icon="\u2713")

        for mail in sorted(fresh, key=ib_sort_key):
            new_mails += 1
            code = ib_extract_code(mail)
            duplicate = bool(code) and code in seen_codes
            if code:
                seen_codes.add(code)
                if not duplicate:
                    new_codes += 1
            accent = IB_ACCENT if duplicate else COLOR_SUCCESS
            title = ("CODE ALREADY SEEN" if duplicate
                     else "NEW STEAM CODE" if code else "NEW MAIL")
            ib_mail_card(mail, title=title, accent=accent, compact=_IB_COMPACT)
            if code:
                if duplicate:
                    ib_log(f"\u041a\u043e\u0434 {code} \u0443\u0436\u0435 \u0432\u0441\u0442\u0440\u0435\u0447\u0430\u043b\u0441\u044f "
                           "\u0432 \u044d\u0442\u043e\u0439 \u0441\u0435\u0441\u0441\u0438\u0438", COLOR_WARN, icon="\u21ba")
                else:
                    ib_log(f"\u041d\u041e\u0412\u042b\u0419 STEAM GUARD \u041a\u041e\u0414: {code}",
                           COLOR_SUCCESS, bold=True, icon="\u2605")
                if not _IB_COMPACT:
                    try:
                        sys.stdout.write("\a")
                        sys.stdout.flush()
                    except Exception:
                        pass
            else:
                ib_log("\u041f\u0438\u0441\u044c\u043c\u043e \u0431\u0435\u0437 Steam Guard \u043a\u043e\u0434\u0430 "
                       "(\u0441\u0441\u044b\u043b\u043a\u0430 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0438\u044f "
                       "\u0438\u043b\u0438 \u0443\u0432\u0435\u0434\u043e\u043c\u043b\u0435\u043d\u0438\u0435)", COLOR_WARN, icon="\u26a0")

        frames = 0
        while time.time() - loop_start < interval:
            if state["quit"].is_set() or state["refresh"].is_set():
                break
            elapsed = time.time() - started
            uptime = f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d}"
            if last_error:
                ib_live_status(f"\u043d\u0435\u0442 \u0441\u0432\u044f\u0437\u0438 \u0441 Gmail \u2022 "
                               f"\u043f\u043e\u0432\u0442\u043e\u0440 \u0447\u0435\u0440\u0435\u0437 "
                               f"{interval - int(time.time() - loop_start)}\u0441 \u2022 "
                               f"\u043f\u0438\u0441\u0435\u043c {new_mails} \u2022 \u043a\u043e\u0434\u043e\u0432 {new_codes}",
                               COLOR_ERROR, frame=IB_SPINNER[frames % len(IB_SPINNER)], highlight=True)
            else:
                ib_live_status(f"\u0441\u043b\u0435\u0436\u0443 \u2022 {uptime} \u2022 "
                               f"\u043f\u0438\u0441\u0435\u043c {new_mails} \u2022 \u043a\u043e\u0434\u043e\u0432 {new_codes} "
                               f"\u2022 \u043f\u0440\u043e\u0432\u0435\u0440\u043e\u043a {scans}",
                               COLOR_DIM, frame=IB_SPINNER[frames % len(IB_SPINNER)])
            frames += 1
            time.sleep(0.1)

    ib_clear_live_status()
    ib_rule(" \u25a0 INBOX STOPPED ")
    ib_log(f"\u0418\u0442\u043e\u0433 \u0441\u0435\u0441\u0441\u0438\u0438 \u0438\u043d\u0431\u043e\u043a\u0441\u0430: "
           f"\u043f\u0438\u0441\u0435\u043c {new_mails}, \u043a\u043e\u0434\u043e\u0432 {new_codes}, "
           f"\u043f\u0440\u043e\u0432\u0435\u0440\u043e\u043a {scans}", COLOR_TEXT)
    _IB_COMPACT = False
    set_console_title(APP_TITLE)
    show_cursor()
    wait_for_enter()


def _capture(fn, *args, **kwargs):
    """Вызывает функцию и возвращает то, что она напечатала в stdout."""
    import io as _io
    import contextlib

    buf = _io.StringIO()
    with contextlib.redirect_stdout(buf):
        fn(*args, **kwargs)
    return buf.getvalue()


def inbox_self_test(verbose=False):
    """Проверяет, что вся отрисовка ровно ложится в ширину консоли."""
    problems = []
    indent = display_width(IB_PANEL_INDENT)
    line_width = indent + IB_WIDTH

    def strip_ansi(text):
        return re.sub(r"\x1b\[[0-9;]*m", "", text)

    def check(label, rendered, expected):
        for line in strip_ansi(rendered).splitlines():
            got = display_width(line)
            if got != expected:
                problems.append(f"{label}: {got} != {expected}")
                break

    check("rule", _capture(ib_rule), line_width)
    check("rule-text", _capture(ib_rule, " NEW MAIL "), line_width)
    check("rule-text-long", _capture(ib_rule, " X " * 400), line_width)
    check("big-code", _capture(lambda: [write(r + "\n") for r in ib_big_text("AB12C")]),
          line_width)
    check("big-code-1", _capture(lambda: [write(r + "\n") for r in ib_big_text("1")]),
          line_width)

    if verbose:
        print(f"console width   : {CONSOLE_WIDTH}")
        print(f"inbox line width: {line_width}")
        print(f"colors          : {'on' if COLOR_ENABLED else 'off'}")
        print()

    if problems:
        print("ALIGNMENT PROBLEMS:")
        for item in problems:
            print("  - " + item)
    else:
        print(f"OK: all rows aligned ({line_width} cols)")
    return problems


def pause_before_exit(message="Press Enter to exit..."):
    show_cursor()
    write("\n  ")
    write(color(message, COLOR_MUTED) + "\n")
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass


def handle_crash():
    show_cursor()
    print_result(False, "Fatal Error", detail=traceback.format_exc().strip())


def wait_for_enter():
    write("\n  " + color("Press Enter to continue...", COLOR_MUTED) + "\n")
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass


def load_settings():
    global HEADLESS_MODE, ACCOUNTS_TOTAL, ACCOUNT_GAP, NONECAP_API_KEY
    global DISCORD_WEBHOOK, COLORS_ENABLED_SETTING, CUSTOM_NAME, AVATAR_ENABLED
    global PROXY_ENABLED, PROXY_VALUE
    parser = configparser.ConfigParser()
    parser["settings"] = dict(DEFAULT_SETTINGS)
    if CONFIG_FILE.exists():
        try:
            parser.read(CONFIG_FILE, encoding="utf-8")
        except configparser.Error:
            pass
    if not parser.has_section("settings"):
        parser["settings"] = dict(DEFAULT_SETTINGS)
    section = parser["settings"]
    HEADLESS_MODE = section.getboolean("headless", fallback=True)
    ACCOUNTS_TOTAL = max(1, section.getint("account_total", fallback=1))
    ACCOUNT_GAP = section.getint("account_gap", fallback=1)
    NONECAP_API_KEY = section.get("nonecap_api_key", fallback="").strip()
    DISCORD_WEBHOOK = section.get("discord_webhook", fallback="").strip()
    CUSTOM_NAME = section.get("custom_name", fallback="").strip()
    AVATAR_ENABLED = section.getboolean("avatar", fallback=True)
    COLORS_ENABLED_SETTING = section.getboolean("colors", fallback=True)
    PROXY_ENABLED = section.getboolean("proxy_enabled", fallback=False)
    PROXY_VALUE = section.get("proxy", fallback="").strip()
    resolve_color_enabled()
    save_settings()


def save_settings():
    parser = configparser.ConfigParser()
    parser["settings"] = {
        "headless": str(HEADLESS_MODE).lower(),
        "account_total": str(ACCOUNTS_TOTAL),
        "account_gap": str(ACCOUNT_GAP),
        "nonecap_api_key": NONECAP_API_KEY,
        "discord_webhook": DISCORD_WEBHOOK,
        "custom_name": CUSTOM_NAME,
        "avatar": str(AVATAR_ENABLED).lower(),
        "colors": str(COLORS_ENABLED_SETTING).lower(),
        "proxy_enabled": str(PROXY_ENABLED).lower(),
        "proxy": PROXY_VALUE,
    }
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            parser.write(f)
    except OSError as e:
        log_line(f"Settings error: {e}", COLOR_ERROR)


def gmail_auth():
    GMAIL_DIR.mkdir(parents=True, exist_ok=True)
    if not GMAIL_CREDS_FILE.exists():
        log_line(
            f"Не найден {GMAIL_CREDS_FILE.name}!\\n"
            "Скачай его в Google Cloud Console:\\n"
            "  APIs & Services -> Credentials -> Create client -> Desktop app -> Download JSON\\n"
            f"и положи в папку {GMAIL_DIR.name} под именем client_secret.json",
            COLOR_ERROR,
        )
        pause_before_exit()
        sys.exit(1)
    conf = json.loads(GMAIL_CREDS_FILE.read_text(encoding="utf-8"))
    conf = conf.get("installed") or conf.get("web") or conf
    log_line("Starting Gmail OAuth...", COLOR_WARN)
    log_line("Откроется браузер — залогинься в аккаунт your_email@gmail.com", COLOR_WARN)
    result = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            result.update({k: v[0] for k, v in q.items()})
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                "<h2>OK, можно закрыть вкладку и вернуться в консоль</h2>".encode("utf-8")
            )
            threading.Thread(target=server.shutdown).start()

        def log_message(self, *args):
            pass

    try:
        server = socketserver.TCPServer(("", GMAIL_PORT), Handler)
    except OSError as e:
        log_line(f"Порт {GMAIL_PORT} занят: {e}", COLOR_ERROR)
        pause_before_exit()
        sys.exit(1)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = GMAIL_AUTH_URL + "?" + urllib.parse.urlencode({
        "client_id": conf["client_id"],
        "redirect_uri": GMAIL_REDIRECT,
        "scope": GMAIL_SCOPES,
        "response_type": "code",
        "access_type": "offline",
        "prompt": "consent",
    })
    log_line(f"Если браузер не открылся, зайди вручную: {url}", COLOR_WARN)
    webbrowser.open(url)
    deadline = time.time() + 300
    while not result.get("code") and not result.get("error"):
        if time.time() > deadline:
            log_line("Таймаут ожидания OAuth (5 мин)", COLOR_ERROR)
            pause_before_exit()
            sys.exit(1)
        time.sleep(0.3)
    try:
        server.server_close()
    except Exception:
        pass
    if result.get("error"):
        log_line(f"Ошибка авторизации: {result['error']}", COLOR_ERROR)
        pause_before_exit()
        sys.exit(1)
    r = requests.post(GMAIL_TOKEN_URL, data={
        "client_id": conf["client_id"],
        "client_secret": conf["client_secret"],
        "code": result["code"],
        "grant_type": "authorization_code",
        "redirect_uri": GMAIL_REDIRECT,
    }, timeout=30).json()
    if "refresh_token" not in r:
        log_line(f"refresh_token не получен: {r}", COLOR_ERROR)
        pause_before_exit()
        sys.exit(1)
    r["expires_at"] = time.time() + r.get("expires_in", 3600)
    GMAIL_TOKEN_FILE.write_text(json.dumps(r, indent=2), encoding="utf-8")
    log_line(f"Gmail OAuth успешно! Токен сохранён в {GMAIL_TOKEN_FILE.name}", COLOR_SUCCESS, bold=True)


def _gmail_access_token():
    if not GMAIL_TOKEN_FILE.exists():
        log_line("token.json не найден — запускаю Gmail OAuth...", COLOR_WARN)
        gmail_auth()
    tok = json.loads(GMAIL_TOKEN_FILE.read_text(encoding="utf-8"))
    if tok.get("expires_at", 0) - 60 > time.time():
        return tok["access_token"]
    conf = json.loads(GMAIL_CREDS_FILE.read_text(encoding="utf-8"))
    conf = conf.get("installed") or conf.get("web") or conf
    r = requests.post(GMAIL_TOKEN_URL, data={
        "client_id": conf["client_id"],
        "client_secret": conf["client_secret"],
        "refresh_token": tok["refresh_token"],
        "grant_type": "refresh_token",
    }, timeout=30).json()
    if "access_token" not in r:
        log_line(f"Не удалось обновить Gmail токен: {r}", COLOR_ERROR)
        log_line("Удаляю token.json — запущу OAuth заново", COLOR_WARN)
        try:
            GMAIL_TOKEN_FILE.unlink()
        except OSError:
            pass
        gmail_auth()
        tok = json.loads(GMAIL_TOKEN_FILE.read_text(encoding="utf-8"))
        return tok["access_token"]
    tok["access_token"] = r["access_token"]
    tok["expires_at"] = time.time() + r.get("expires_in", 3600)
    GMAIL_TOKEN_FILE.write_text(json.dumps(tok, indent=2), encoding="utf-8")
    return tok["access_token"]


def _gmail_parts(payload, out=None):
    out = [] if out is None else out
    if payload.get("parts"):
        for p in payload["parts"]:
            _gmail_parts(p, out)
    elif payload.get("body", {}).get("data"):
        charset = payload.get("charset") or "utf-8"
        raw = base64.urlsafe_b64decode(payload["body"]["data"])
        out.append((payload.get("mimeType", ""), raw.decode(charset, "ignore")))
    return out


def gmail_mails(query, limit=10):
    access = _gmail_access_token()
    hdr = {"Authorization": "Bearer " + access}
    resp = requests.get(f"{GMAIL_API}/messages", headers=hdr,
                        params={"q": query, "maxResults": limit}, timeout=30)
    if resp.status_code != 200:
        log_line(f"Gmail API {resp.status_code}: {resp.text[:300]}", COLOR_ERROR)
        return []
    out = []
    for m in resp.json().get("messages", []):
        d = requests.get(f"{GMAIL_API}/messages/{m['id']}", headers=hdr,
                         params={"format": "full"}, timeout=30).json()
        payload = d.get("payload", {})
        raw_headers = payload.get("headers") or payload.get("header") or []
        head = {}
        for h in raw_headers:
            if isinstance(h, dict):
                head[h.get("name", "").lower()] = h.get("value", "")
            else:
                name, value = h
                head[name.lower()] = value
        text = ""
        for mime, body in _gmail_parts(payload):
            if mime in ("text/plain", "text/html"):
                text += body
                if mime == "text/plain":
                    break
        out.append({
            "id": m["id"],
            "date": head.get("date", ""),
            "from": head.get("from", ""),
            "to": head.get("to", ""),
            "subject": head.get("subject", ""),
            "text": text,
        })
    return out


def parse_mail_date_ms(raw_date):
    """
    Разбирает Date-заголовок письма в epoch-миллисекунды.
    Возвращает 0, если дату не удалось распознать.
    """
    if not raw_date:
        return 0
    cleaned = re.sub(r"\s*\([^)]*\)\s*$", "", raw_date.strip())
    for fmt in ("%a, %d %b %Y %H:%M:%S %z",
                "%a, %d %b %Y %H:%M:%S %Z",
                "%d %b %Y %H:%M:%S %z",
                "%a, %d %b %Y %H:%M:%S"):
        try:
            date_dt = datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
        # Без таймзоны считаем как UTC — иначе свежесть определить нельзя
        if date_dt.tzinfo is None:
            date_dt = date_dt.replace(tzinfo=timezone.utc)
        return int(date_dt.timestamp() * 1000)
    return 0


def newest_fresh_mail(query=None, max_age=MAIL_MAX_AGE):
    """
    Самое свежее письмо, пришедшее не более max_age секунд назад.
    Всё остальное игнорируется — старые письма нам не нужны,
    иначе можно подхватить ссылку от предыдущей попытки.
    Возвращает None, если такого письма нет.
    """
    try:
        mails = gmail_mails(query or GMAIL_QUERY, limit=10)
    except Exception as e:
        log_line(f"Gmail error: {e}", COLOR_ERROR)
        return None

    cutoff_ms = int(time.time() * 1000) - int(max_age * 1000)

    best, best_ms = None, None
    for mail in mails:
        ms = parse_mail_date_ms(mail.get("date"))
        if ms <= 0 or ms < cutoff_ms:
            continue
        if best_ms is None or ms > best_ms:
            best, best_ms = mail, ms

    if best is None:
        return None

    result = dict(best)
    result["internal_ms"] = best_ms
    return result


def gmail_inbox_mails(limit=8, query=None):
    out = []
    try:
        mails = gmail_mails(query or GMAIL_QUERY, limit=limit)
    except Exception as e:
        log_line(f"Gmail error: {e}", COLOR_ERROR)
        return []
    for mail in mails:
        raw_date = mail.get("date") or ""
        internal_ms = parse_mail_date_ms(raw_date)
        out.append({
            "id": mail.get("id", ""),
            "date": raw_date,
            "date_dt": datetime.fromtimestamp(internal_ms / 1000) if internal_ms else None,
            "internal_ms": internal_ms,
            "from": mail.get("from", ""),
            "subject": mail.get("subject", ""),
            "text": mail.get("text", ""),
            "html": "",
        })
    return out


def find_links(text, host_filter=None):
    found = []
    for u in URL_RE.findall(text):
        u = u.rstrip(".,;:!?")
        if host_filter and host_filter not in urllib.parse.urlparse(u).netloc:
            continue
        if u not in found:
            found.append(u)
    return found


def get_steam_confirm_link(timeout=90, interval=1):
    """
    Ждёт ссылку подтверждения в САМОМ свежем письме.
    Берём только то письмо, которому не больше MAIL_MAX_AGE секунд —
    так мы не подхватим старую ссылку от предыдущей попытки.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            mail = newest_fresh_mail(GMAIL_QUERY)
            if mail:
                links = find_links(mail.get("text") or "", GMAIL_HOST_FILTER)
                if links:
                    verify = [u for u in links
                              if "verify" in u.lower() or "confirm" in u.lower()]
                    link = verify[0] if verify else links[0]
                    age = (time.time() * 1000 - mail["internal_ms"]) / 1000
                    log_line(f"Confirm link found (mail age {age:.1f}s)",
                             COLOR_SUCCESS)
                    return link
        except Exception as e:
            log_line(f"Gmail error: {e}", COLOR_ERROR)
        time.sleep(interval)
    return None


def random_login(length=12):
    login = random.choice(string.ascii_letters)
    login += ''.join(random.choices(string.ascii_letters + string.digits, k=length - 1))
    while True:
        shuffled = list(login[1:])
        random.shuffle(shuffled)
        candidate = login[0] + ''.join(shuffled)
        if candidate != login or length <= 2:
            return candidate


def gen_password(length=12):
    if length < 8:
        length = 8
    alphabet = string.ascii_letters + string.digits
    while True:
        pwd = ''.join(random.choices(alphabet, k=length))
        if (any(c.isalpha() for c in pwd)
                and any(c.isdigit() for c in pwd)
                and all(c in alphabet for c in pwd)):
            if any(c.islower() for c in pwd) and any(c.isupper() for c in pwd):
                return pwd


def get_hcaptcha_sitekey(page, timeout=FAST_CAPTCHA_TIMEOUT):
    try:
        page.wait_for_selector('iframe[src*="hcaptcha"], [data-sitekey]', timeout=timeout)
        sitekey = page.evaluate("""() => {
            const hcaptchaDiv = document.querySelector('[data-sitekey]');
            if (hcaptchaDiv) return hcaptchaDiv.getAttribute('data-sitekey');
            return null;
        }""")
        if sitekey:
            return sitekey
        sitekey = page.evaluate("""() => {
            const iframes = document.querySelectorAll('iframe[src*="hcaptcha"]');
            for (const iframe of iframes) {
                const match = iframe.src.match(/sitekey=([a-zA-Z0-9_-]+)/);
                if (match) return match[1];
            }
            return null;
        }""")
        return sitekey
    except Exception:
        return None


def inject_captcha_token(page, token):
    page.evaluate(f"""(token) => {{
        const hcaptchaResp = document.querySelector('[name="h-captcha-response"]');
        if (hcaptchaResp) {{
            hcaptchaResp.value = token;
            hcaptchaResp.innerHTML = token;
        }}
        const gRecaptchaResp = document.querySelector('[name="g-recaptcha-response"]');
        if (gRecaptchaResp) {{
            gRecaptchaResp.value = token;
            gRecaptchaResp.innerHTML = token;
        }}
        if (window.hcaptcha) {{
            window.hcaptcha.getResponse = () => token;
            try {{
                const widgets = window.hcaptcha.widgets || {{}};
                for (const wId in widgets) {{
                    const w = widgets[wId];
                    if (w && w.options && w.options.callback) {{
                        w.options.callback(token);
                    }}
                }}
            }} catch(e) {{}}
        }}
        const iframe = document.querySelector('iframe[data-hcaptcha-widget-id]');
        if (iframe) {{
            iframe.setAttribute('data-hcaptcha-response', token);
            try {{
                iframe.contentWindow.postMessage({{ type: 'hcaptcha', token: token }}, '*');
            }} catch(e) {{}}
        }}
        if (hcaptchaResp) {{
            ['input', 'change', 'blur'].forEach(evtName => {{
                hcaptchaResp.dispatchEvent(new Event(evtName, {{ bubbles: true }}));
            }});
        }}
        const form = document.querySelector('form');
        if (form) {{
            form.dispatchEvent(new Event('change', {{ bubbles: true }}));
        }}
    }}""", token)


def solve_captcha_only(sitekey, url):
    try:
        nc = NoneCap(api_key=NONECAP_API_KEY)
        solve = nc.solve(type="hcaptcha", sitekey=sitekey, url=url)
        token = solve.token
        user_agent = solve.user_agent if hasattr(solve, 'user_agent') else None
        log_line("Captcha Solved...", COLOR_SUCCESS)
        return token, user_agent
    except Exception as e:
        log_line(f"NoneCap solve failed: {e}", COLOR_ERROR)
        return None, None


def avatar_files():
    if not AVATAR_DIR.exists():
        return []
    found = []
    for path in sorted(AVATAR_DIR.iterdir()):
        if path.is_file() and path.suffix.lower() in AVATAR_EXTENSIONS:
            found.append(path)
    found.sort(key=lambda p: (0 if p.suffix.lower() == ".png" else 1, p.name.lower()))
    return found


def pick_avatar_file():
    files = avatar_files()
    return files[0] if files else None


def ensure_avatar_dir():
    try:
        AVATAR_DIR.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        log_line(f"Could not create {AVATAR_DIR.name} folder: {e}", COLOR_ERROR)
        return False


def send_to_discord(login, password, email, steamid=""):
    if not DISCORD_WEBHOOK:
        return
    try:
        fields = [
            {"name": "Login", "value": f"```{login}```", "inline": True},
            {"name": "Password", "value": f"```{password}```", "inline": True},
            {"name": "Email", "value": f"```{email}```", "inline": False},
        ]
        if steamid:
            fields.append({"name": "SteamID64", "value": f"```{steamid}```", "inline": False})
        embed = {
            "title": "New Steam Account Created",
            "color": 5814783,
            "fields": fields,
            "footer": {"text": "Generated by Xetaon"},
            "timestamp": "",
        }
        r = requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]}, timeout=10)
        if r.status_code in (200, 204):
            log_line("Discord: sent", COLOR_SUCCESS)
        else:
            log_line(f"Discord: error {r.status_code}", COLOR_ERROR)
    except Exception as e:
        log_line(f"Discord: not sent ({e})", COLOR_ERROR)


def _kill_pid_tree(pid):
    try:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                       capture_output=True, timeout=5)
    except Exception:
        pass


def kill_chrome_by_profile(profile_dir):
    if os.name != "nt" or profile_dir is None:
        return
    profile_name = Path(profile_dir).name
    pids = set()

    # wmic выпилили из свежих Windows 11, поэтому сначала PowerShell + CIM.
    ps_script = (
        "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe' or Name='msedge.exe'\" | "
        "Where-Object { $_.CommandLine -like '*__PROFILE__*' } | "
        "Select-Object -ExpandProperty ProcessId"
    ).replace("__PROFILE__", profile_name)
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
            capture_output=True, timeout=20,
        )
        # PowerShell пишет в OEM-кодировке, а не в UTF-8 — декодируем без падений.
        for line in result.stdout.decode("utf-8", "ignore").splitlines():
            line = line.strip()
            if line.isdigit():
                pids.add(line)
    except Exception:
        pass

    if not pids:
        try:
            result = subprocess.run(
                ["wmic", "process", "where",
                 f"name='chrome.exe' and CommandLine like '%{profile_name}%'",
                 "get", "ProcessId"],
                capture_output=True, timeout=10,
            )
            for line in result.stdout.decode("utf-8", "ignore").splitlines():
                line = line.strip()
                if line.isdigit():
                    pids.add(line)
        except Exception:
            pass

    for pid in pids:
        _kill_pid_tree(pid)
    if pids:
        log_line(f"Killed leftover browser processes for profile "
                 f"{profile_name}: {len(pids)}", COLOR_WARN)
    time.sleep(0.1)


def clear_profile_locks(profile_dir):
    if profile_dir is None or not profile_dir.exists():
        return
    for lock in profile_dir.glob("Singleton*"):
        try:
            lock.unlink()
        except OSError:
            pass


def remove_profile_dir(profile_dir):
    if profile_dir is None or not profile_dir.exists():
        return
    for attempt in range(3):
        try:
            shutil.rmtree(profile_dir, ignore_errors=False)
            log_line(f"Profile removed: {profile_dir.name}", COLOR_SUCCESS)
            return
        except Exception as e:
            if attempt < 2:
                time.sleep(0.3)
            else:
                try:
                    shutil.rmtree(profile_dir, ignore_errors=True)
                    if not profile_dir.exists():
                        log_line(f"Profile removed (forced): {profile_dir.name}", COLOR_SUCCESS)
                        return
                except Exception:
                    pass
                log_line(f"Failed to remove profile: {e}", COLOR_WARN)


CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    rf"{os.environ.get('LOCALAPPDATA', '')}\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]

# Edge — тоже Chromium: CDP работает точно так же.
EDGE_PATHS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def find_chrome_executable():
    """
    Ищет браузер для генерации: Chrome → Chromium от Playwright → Edge.

    Раньше брался ТОЛЬКО системный Chrome. Если его нет, программа
    падала с "Chrome executable not found", хотя Chromium уже лежит
    рядом, скачанный Playwright'ом. Плюс можно задать свой путь через
    переменную окружения STEAMACCGEN_CHROME.
    """
    candidates = []
    override = os.environ.get("STEAMACCGEN_CHROME", "").strip()
    if override:
        candidates.append(override)
    candidates.extend(CHROME_PATHS)

    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        pw_root = Path(local) / "ms-playwright"
        if pw_root.exists():
            for pattern in ("chromium-*/chrome-win64/chrome.exe",
                            "chromium-*/chrome-win/chrome.exe"):
                candidates.extend(str(p) for p in
                                  sorted(pw_root.glob(pattern), reverse=True))

    candidates.extend(EDGE_PATHS)
    for path in candidates:
        if path and Path(path).exists():
            return path
    return None


# Выносим наружу, чтобы переиспользовать по всему модулю
CHROME_EXE = find_chrome_executable()


def find_free_port():
    """Свободный локальный порт для CDP, чтобы не воевать с прошлым Chrome."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def parse_proxy(raw):
    """Разбирает строку прокси. Возвращает dict или None, если формат кривой."""
    raw = (raw or "").strip()
    if not raw:
        return None
    match = PROXY_RE.match(raw)
    if not match:
        return None
    scheme = (match.group("scheme") or "http").lower()
    if scheme not in PROXY_SCHEMES:
        return None
    port = int(match.group("port"))
    if not 1 <= port <= 65535:
        return None
    host = match.group("host")
    user = match.group("user") or ""
    password = match.group("password") or ""
    chrome_scheme = PROXY_SCHEMES[scheme]
    server = f"{chrome_scheme}://{host}:{port}"
    auth = f"{user}:{password}@" if user else ""
    return {
        "scheme": chrome_scheme,
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "server": server,
        "url": f"{chrome_scheme}://{auth}{host}:{port}",
        "display": f"{chrome_scheme}://{host}:{port}" + (" [auth]" if user else ""),
    }


def proxy_candidates():
    """Все валидные прокси из настройки (можно список через , ; или перенос строки)."""
    out = []
    for chunk in re.split(r"[,;\r\n]+", PROXY_VALUE or ""):
        parsed = parse_proxy(chunk)
        if parsed:
            out.append(parsed)
    return out


def pick_proxy():
    """Прокси для очередного запуска Chrome. Без проверок — что вписал, то и поедет."""
    if not PROXY_ENABLED:
        return None
    chunks = [c for c in re.split(r"[,;\r\n]+", PROXY_VALUE or "") if c.strip()]
    if not chunks:
        return None
    raw = random.choice(chunks)
    parsed = parse_proxy(raw)
    if parsed:
        return parsed
    server = raw if "://" in raw else f"http://{raw}"
    return {
        "scheme": "http",
        "host": raw,
        "port": 0,
        "user": "",
        "password": "",
        "server": server,
        "url": server,
        "display": server,
    }


def mask_proxy(raw):
    """Скрывает логин/пароль в строке прокси для логов и меню."""
    parsed = parse_proxy(raw)
    if not parsed:
        return raw or "[NOT SET]"
    return parsed["display"]


def summarize_proxy(raw):
    """Короткая подпись для меню: первый прокси + количество из списка."""
    chunks = [c for c in re.split(r"[,;\r\n]+", raw or "") if c.strip()]
    if not chunks:
        return "[NOT SET]"
    label = mask_proxy(chunks[0])
    return label + (f" (+{len(chunks) - 1})" if len(chunks) > 1 else "")


def check_proxy(parsed, timeout=15):
    """Проверка прокси запросом наружу. Возвращает (ok, текст)."""
    if parsed["scheme"].startswith("socks"):
        try:
            import socks  # noqa: F401  (PySocks)
        except Exception:
            return False, "PySocks не установлен: py -m pip install pysocks"
    proxies = {"http": parsed["url"], "https": parsed["url"]}
    try:
        started = time.time()
        resp = requests.get("https://api.ipify.org", proxies=proxies, timeout=timeout)
        ms = int((time.time() - started) * 1000)
        if resp.status_code == 200:
            return True, f"IP: {resp.text.strip()} ({ms} ms)"
        return False, f"HTTP {resp.status_code}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def _recv_exact(sock, count):
    buf = b""
    while len(buf) < count:
        chunk = sock.recv(count - len(buf))
        if not chunk:
            raise ConnectionError("upstream closed connection")
        buf += chunk
    return buf


class ProxyRelay(threading.Thread):
    """
    Локальный HTTP-прокси для Chrome.
    Chrome не умеет передавать логин/пароль в --proxy-server, поэтому Chrome
    ходит на 127.0.0.1:<port>, а релей сам логинится в апстрим
    (HTTP CONNECT с Proxy-Authorization или SOCKS5 с авторизацией).
    """

    def __init__(self, upstream, host="127.0.0.1"):
        super().__init__(daemon=True)
        self.upstream = upstream
        self._stop_evt = threading.Event()
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind((host, 0))
        self._server.listen(64)
        self._server.settimeout(0.5)
        self.port = self._server.getsockname()[1]

    def stop(self):
        self._stop_evt.set()
        try:
            self._server.close()
        except OSError:
            pass

    def run(self):
        while not self._stop_evt.is_set():
            try:
                client, _ = self._server.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            client.settimeout(30)
            threading.Thread(target=self._serve, args=(client,), daemon=True).start()

    # ---------- апстрим ----------
    def _open_upstream(self):
        up = self.upstream
        sock = socket.create_connection((up["host"], up["port"]), timeout=20)
        if up["scheme"] == "https":
            ctx = ssl.create_default_context()
            sock = ctx.wrap_socket(sock, server_hostname=up["host"])
        sock.settimeout(30)
        return sock

    def _socks5_connect(self, sock, host, port):
        up = self.upstream
        user = up["user"].encode()
        password = up["password"].encode()
        methods = b"\x00\x02" if user else b"\x00"
        sock.sendall(b"\x05" + bytes([len(methods)]) + methods)
        _, method = _recv_exact(sock, 2)
        if method == 0x02:
            sock.sendall(b"\x01" + bytes([len(user)]) + user
                         + bytes([len(password)]) + password)
            _, status = _recv_exact(sock, 2)
            if status != 0:
                raise ConnectionError("socks5 auth rejected")
        elif method != 0x00:
            raise ConnectionError("socks5: no acceptable auth method")
        host_bytes = host.encode("idna") if host else b""
        sock.sendall(b"\x05\x01\x00\x03" + bytes([len(host_bytes)]) + host_bytes
                     + int(port).to_bytes(2, "big"))
        _, rep, _, atyp = _recv_exact(sock, 4)
        if rep != 0:
            raise ConnectionError(f"socks5 connect failed (rep={rep})")
        if atyp == 0x01:
            _recv_exact(sock, 4)
        elif atyp == 0x03:
            _recv_exact(sock, _recv_exact(sock, 1)[0])
        elif atyp == 0x04:
            _recv_exact(sock, 16)
        _recv_exact(sock, 2)

    def _http_connect(self, sock, host, port):
        up = self.upstream
        target = f"{host}:{port}"
        head = f"CONNECT {target} HTTP/1.1\r\nHost: {target}\r\n"
        if up["user"]:
            raw = f"{up['user']}:{up['password']}".encode()
            head += "Proxy-Authorization: Basic "\
                    + base64.b64encode(raw).decode() + "\r\n"
        head += "Proxy-Connection: keep-alive\r\n\r\n"
        sock.sendall(head.encode("latin-1"))
        resp = b""
        while b"\r\n\r\n" not in resp:
            chunk = sock.recv(4096)
            if not chunk:
                raise ConnectionError("http proxy closed connection")
            resp += chunk
            if len(resp) > 65536:
                raise ConnectionError("http proxy response too big")
        status_line = resp.split(b"\r\n", 1)[0].decode("latin-1", "replace")
        parts = status_line.split(" ")
        code = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        if code != 200:
            raise ConnectionError(f"http proxy refused CONNECT: {status_line}")

    def _connect_target(self, host, port):
        sock = self._open_upstream()
        try:
            if self.upstream["scheme"].startswith("socks"):
                self._socks5_connect(sock, host, port)
            else:
                self._http_connect(sock, host, port)
        except Exception:
            try:
                sock.close()
            except OSError:
                pass
            raise
        return sock

    # ---------- клиент ----------
    def _serve(self, client):
        upstream = None
        try:
            head = b""
            while b"\r\n\r\n" not in head:
                chunk = client.recv(8192)
                if not chunk:
                    return
                head += chunk
                if len(head) > 131072:
                    return

            lines = head.split(b"\r\n")
            parts = lines[0].decode("latin-1", "replace").split(" ")
            if len(parts) < 3:
                return
            method, target, version = parts[0], parts[1], parts[2]

            if method.upper() == "CONNECT":
                host, _, port = target.rpartition(":")
                try:
                    upstream = self._connect_target(host.strip("[]"), int(port or 443))
                except Exception:
                    self._reply(client, b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                    return
                client.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
                self._pipe(client, upstream)
                return

            parsed = urllib.parse.urlsplit(target)
            if not parsed.hostname:
                client.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
                return
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            path = (parsed.path or "/") + (f"?{parsed.query}" if parsed.query else "")
            try:
                upstream = self._connect_target(parsed.hostname, port)
            except Exception:
                self._reply(client, b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                return

            rebuilt = [f"{method} {path} {version}".encode("latin-1")]
            for line in lines[1:]:
                if not line:
                    continue
                low = line.lower()
                if low.startswith(b"proxy-connection:") or \
                        low.startswith(b"proxy-authorization:"):
                    continue
                rebuilt.append(line)
            upstream.sendall(b"\r\n".join(rebuilt) + b"\r\n\r\n")
            leftover = head.split(b"\r\n\r\n", 1)[1]
            if leftover:
                upstream.sendall(leftover)
            self._pipe(client, upstream)
        except Exception:
            return
        finally:
            for sock in (client, upstream):
                if sock is None:
                    continue
                try:
                    sock.close()
                except OSError:
                    pass

    @staticmethod
    def _reply(client, data):
        try:
            client.sendall(data)
        except OSError:
            pass

    def _pipe(self, a, b):
        pair = [a, b]
        try:
            while not self._stop_evt.is_set():
                ready, _, _ = select.select(pair, [], [], 0.5)
                if not ready:
                    continue
                for sock in ready:
                    data = sock.recv(65536)
                    if not data:
                        return
                    (b if sock is a else a).sendall(data)
        except (OSError, ValueError):
            return


def launch_chrome_with_cdp(profile_dir):
    global CHROME_EXE
    if not CHROME_EXE or not Path(CHROME_EXE).exists():
        CHROME_EXE = find_chrome_executable()
    chrome = CHROME_EXE
    if not chrome:
        log_line("Браузер не найден: Chrome / Chromium (Playwright) / Edge",
                 COLOR_ERROR)
        log_line("Поставь Chrome или выполни: py -m playwright install chromium",
                 COLOR_WARN)
        pause_before_exit()
        sys.exit(1)
    kill_chrome_by_profile(profile_dir)
    clear_profile_locks(profile_dir)
    profile_dir.mkdir(parents=True, exist_ok=True)
    cdp_port = find_free_port()
    args = [
        chrome,
        f"--user-data-dir={profile_dir}",
        f"--remote-debugging-port={cdp_port}",
        "--remote-allow-origins=*",
        f"--window-size={WINDOW_SIZE}",
        "--disable-logging",
        "--log-level=3",
        "--disable-gpu",
        "--disable-software-rasterizer",
        "--disable-dev-shm-usage",
        "--silent",
        "--disable-extensions",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-networking",
        "--disable-background-timer-throttling",
        "--disable-renderer-backgrounding",
        "--disable-backgrounding-occluded-windows",
        "--disable-ipc-flooding-protection",
        "--disable-hang-monitor",
        "--disable-prompt-on-repost",
        "--disable-sync",
        "--metrics-recording-only",
        "--password-store=basic",
        "--use-mock-keychain",
        "--disable-features=Translate,MediaRouter,OptimizationHints",
        "--disable-component-update",
        "--no-pings",
    ]
    proxy = pick_proxy()
    relay = None
    if proxy and proxy["user"] and proxy["scheme"] in ("http", "https", "socks5"):
        try:
            relay = ProxyRelay(proxy)
            relay.start()
            log_line(f"Proxy relay 127.0.0.1:{relay.port} -> {proxy['display']}",
                     COLOR_SUCCESS)
        except Exception as e:
            relay = None
            log_line(f"Proxy relay failed: {e}", COLOR_ERROR)
    if proxy:
        server = f"http://127.0.0.1:{relay.port}" if relay else proxy["server"]
        args.append(f"--proxy-server={server}")
        args.append("--proxy-bypass-list=localhost;127.0.0.1")
    if HEADLESS_MODE:
        args.append("--headless=new")
        args.append("--no-startup-window")
        log_line("Chrome: headless mode", COLOR_SUCCESS)
    else:
        log_line("Chrome: visible mode", COLOR_SUCCESS)
    if proxy:
        log_line(f"Chrome: proxy {proxy['display']}", COLOR_SUCCESS)
    else:
        log_line("Chrome: direct connection", COLOR_WARN)
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NO_WINDOW
    try:
        proc = subprocess.Popen(
            args,
            startupinfo=startupinfo,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
        )
        proc.proxy_relay = relay
        log_line(f"Chrome PID: {proc.pid}, CDP port {cdp_port}")
        deadline = time.time() + max(FAST_CDP_WAIT, 5.0)
        cdp_ready = False
        while time.time() < deadline:
            if proc.poll() is not None:
                log_line(f"Chrome exited immediately (code {proc.returncode})",
                         COLOR_ERROR)
                break
            try:
                r = requests.get(f"http://127.0.0.1:{cdp_port}/json/version",
                                 timeout=0.5)
                if r.status_code == 200:
                    cdp_ready = True
                    break
            except Exception:
                pass
            time.sleep(0.1)
        if not cdp_ready:
            log_line(f"CDP did not come up on port {cdp_port}", COLOR_ERROR)
        return proc, cdp_port
    except Exception as e:
        log_line(f"Failed to launch Chrome: {e}", COLOR_ERROR)
        if relay is not None:
            relay.stop()
        pause_before_exit()
        sys.exit(1)


def kill_chrome_proc(proc, profile_dir):
    relay = getattr(proc, "proxy_relay", None) if proc is not None else None
    if relay is not None:
        relay.stop()
    if proc is not None:
        try:
            proc.kill()
            proc.wait(timeout=3)
            log_line("Chrome killed", COLOR_SUCCESS)
        except Exception:
            pass
    kill_chrome_by_profile(profile_dir)


def click_visible_button_by_text(page, texts):
    try:
        for t in texts:
            for sel in [f"button:has-text('{t}')", f"a:has-text('{t}')",
                        f"input[type='submit'][value*='{t}']"]:
                try:
                    loc = page.locator(sel)
                    n = loc.count()
                    for i in range(n):
                        el = loc.nth(i)
                        if el.is_visible():
                            el.scroll_into_view_if_needed()
                            time.sleep(0.05)
                            el.click()
                            log_line(f"Clicked button: '{t}'", COLOR_SUCCESS)
                            return True
                except Exception:
                    continue
    except Exception as e:
        log_line(f"click_visible_button_by_text error: {e}", COLOR_ERROR)
    return False


def get_steamid64_from_page(page, timeout=15):
    if not open_page_fully(page, "https://steamcommunity.com/my/profile",
                           timeout=20, scroll=False, retries=2):
        log_line("Failed to open /my/profile", COLOR_ERROR)
        return None
    deadline = time.time() + timeout
    while time.time() < deadline:
        url = page.url
        m = STEAMID64_RE.search(url)
        if m:
            return m.group(1)
        try:
            sid = page.evaluate("""() => {
                if (window.g_rgProfileData && window.g_rgProfileData.steamid) {
                    return window.g_rgProfileData.steamid;
                }
                if (window.g_steamID) return window.g_steamID;
                const m = document.documentElement.innerHTML.match(/7656119\\d{10}/);
                return m ? m[0] : null;
            }""")
            if sid:
                return sid
        except Exception:
            pass
        time.sleep(0.15)
    return None


def find_profile_name_input(page):
    candidates = [
        "#persona_name", "#personaName",
        "input[name='personaName']", "input[name='persona_name']",
    ]
    for sel in candidates:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0 and loc.is_visible():
                return loc
        except Exception:
            continue
    labels = [
        "Profile name", "Имя профиля", "个人资料名称", "プロフィール名",
        "프로필 이름", "Profilname", "Nombre del perfil", "Nome del profilo",
        "Nom du profil", "Nome do perfil"
    ]
    for label in labels:
        try:
            label_loc = page.locator(f"text='{label}'").first
            if label_loc.count() == 0:
                continue
            handle = label_loc.element_handle()
            if handle is None:
                continue
            inp = page.evaluate_handle("""(labelEl) => {
                let parent = labelEl.parentElement;
                for (let i = 0; i < 5 && parent; i++) {
                    const inp = parent.querySelector('input[type=text], input:not([type]), textarea');
                    if (inp && inp.offsetParent !== null) return inp;
                    parent = parent.parentElement;
                }
                return null;
            }""", handle)
            el = inp.as_element()
            if el is not None:
                return el
        except Exception:
            continue
    try:
        el = page.evaluate_handle("""() => {
            const inputs = Array.from(document.querySelectorAll('input[type=text], input:not([type])'));
            for (const inp of inputs) {
                if (inp.maxLength === 32 && inp.offsetParent !== null) return inp;
            }
            return null;
        }""").as_element()
        if el is not None:
            return el
    except Exception:
        pass
    return None


def wait_for_full_page_load(page, timeout=20, scroll=False):
    deadline = time.time() + timeout
    try:
        page.wait_for_load_state("load", timeout=max(2000, int(timeout * 1000 * 0.6)))
    except Exception:
        pass
    while time.time() < deadline:
        try:
            state = page.evaluate("""() => ({
                ready: document.readyState,
                fonts: document.fonts ? document.fonts.status : "loaded",
                height: Math.max(document.body ? document.body.scrollHeight : 0,
                                 document.documentElement.scrollHeight)
            })""")
            if state.get("ready") == "complete" and state.get("fonts") == "loaded":
                if scroll:
                    page.evaluate("""async () => {
                        const step = Math.max(250, window.innerHeight);
                        for (let y = 0; y <= document.body.scrollHeight; y += step) {
                            window.scrollTo(0, y);
                            await new Promise(r => setTimeout(r, 80));
                        }
                        window.scrollTo(0, 0);
                    }""")
                try:
                    page.wait_for_load_state("networkidle", timeout=3000)
                except Exception:
                    pass
                return True
        except Exception:
            pass
        time.sleep(0.15)
    return False


def open_page_fully(page, url, timeout=20, scroll=False, retries=2):
    for attempt in range(1, max(1, retries) + 1):
        wait_mode = "domcontentloaded" if attempt == 1 else "load"
        if attempt > 1:
            log_line(f"Reloading page (try {attempt}/{retries}): {truncate_plain(url, 80)}",
                     COLOR_WARN)
        try:
            page.goto(url, wait_until=wait_mode, timeout=timeout * 1000)
        except Exception as e:
            log_line(f"goto failed ({url}): {truncate_plain(str(e), 120)}", COLOR_WARN)
            time.sleep(0.3)
            continue
        try:
            page.wait_for_load_state("load", timeout=timeout * 1000)
        except Exception:
            pass
        if not wait_for_full_page_load(page, timeout=timeout, scroll=scroll):
            log_line(f"Page did not finish loading: {url}", COLOR_WARN)
            continue
        log_line(f"Page fully loaded: {truncate_plain(page.url, 90)}", COLOR_SUCCESS)
        return True
    log_line(f"Failed to load page after {retries} tries: {url}", COLOR_ERROR)
    return False


def set_profile_avatar(page, steamid64, image_path):
    url = f"https://steamcommunity.com/profiles/{steamid64}/edit/avatar"
    log_line(f"Opening edit/avatar: {url}")
    if not open_page_fully(page, url, timeout=20, scroll=False, retries=2):
        return False
    log_line(f"Avatar file to upload: {image_path.name} "
             f"({image_path.stat().st_size // 1024} KB)")

    file_input = None
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            inputs = page.locator("input[type=file]")
            count = inputs.count()
        except Exception:
            count = 0
        for i in range(count):
            try:
                handle = inputs.nth(i).element_handle()
                if handle is not None:
                    file_input = handle
                    break
            except Exception:
                continue
        if file_input is not None:
            break
        time.sleep(0.2)

    try:
        if file_input is not None:
            file_input.set_input_files(str(image_path))
            log_line("Avatar file attached to upload input", COLOR_SUCCESS)
        else:
            opener = None
            for text in ("Upload your avatar", "Загрузите свой аватар",
                         "Загрузить аватар", "Upload", "Загрузить"):
                try:
                    candidate = page.get_by_text(text, exact=False).first
                    if candidate.count() > 0 and candidate.is_visible():
                        opener = candidate
                        break
                except Exception:
                    continue
            if opener is None:
                log_line("Avatar upload control not found", COLOR_ERROR)
                return False
            log_line("Clicking 'Upload your avatar' and choosing the file...")
            with page.expect_file_chooser() as chooser_info:
                opener.click()
            chooser_info.value.set_files(str(image_path))
            log_line("Avatar file selected in file dialog", COLOR_SUCCESS)
    except Exception as e:
        log_line(f"Avatar upload error: {truncate_plain(str(e), 120)}", COLOR_ERROR)
        return False

    log_line("Waiting for Steam to upload and process the image...")
    try:
        page.wait_for_load_state("load", timeout=40000)
    except Exception:
        pass
    wait_for_full_page_load(page, timeout=30, scroll=False)
    time.sleep(0.8)

    saved = click_visible_button_by_text(page, [
        "Save", "Сохранить", "保存", "Сохранить изменения",
    ])
    if not saved:
        log_line("Save button for avatar not found", COLOR_ERROR)
        return False
    log_line("Clicked Save for avatar", COLOR_SUCCESS)
    try:
        page.wait_for_load_state("load", timeout=20000)
    except Exception:
        pass
    time.sleep(0.8)

    try:
        error_box = page.locator("#error_display, .error_ctn").first
        if error_box.count() > 0 and error_box.is_visible():
            err_text = error_box.inner_text().strip()
            if err_text:
                log_line(f"Avatar error from Steam: {truncate_plain(err_text, 120)}",
                         COLOR_ERROR)
                return False
    except Exception:
        pass

    if open_page_fully(page, f"https://steamcommunity.com/profiles/{steamid64}",
                       timeout=20, scroll=False, retries=2):
        src = ""
        try:
            src = page.evaluate("""() => {
                const img = document.querySelector('.playerAvatarAutoSizeInner img, .profile_header_avatar img');
                return img ? img.src : '';
            }""")
        except Exception:
            pass
        lowered = (src or "").lower()
        if not src or "default" in lowered or "holder" in lowered:
            log_line(f"Avatar does not look updated (src: {truncate_plain(lowered, 90)})",
                     COLOR_WARN)
            return False
        log_line("Avatar confirmed on the profile page", COLOR_SUCCESS, bold=True)
        return True
    log_line("Could not verify avatar (profile page not loaded)", COLOR_WARN)
    return False


def set_profile_name(page, steamid64, new_name, timeout=15):
    url = f"https://steamcommunity.com/profiles/{steamid64}/edit/info"
    log_line(f"Opening edit/info: {url}")

    if not open_page_fully(page, url, timeout=20, scroll=True, retries=2):
        return False

    name_input = None
    deadline = time.time() + max(8, timeout)
    while time.time() < deadline and name_input is None:
        name_input = find_profile_name_input(page)
        if name_input is None:
            time.sleep(0.2)
    if name_input is None:
        log_line("Profile name input not found", COLOR_ERROR)
        return False
    log_line("Profile name field is ready", COLOR_SUCCESS)

    try:
        name_input.scroll_into_view_if_needed()
        time.sleep(0.1)
        name_input.click()
        try:
            name_input.fill("")
        except Exception:
            name_input.press("Control+A")
            name_input.press("Delete")
        time.sleep(0.1)
        name_input.type(new_name, delay=25)
        log_line(f"Filled profile name: {new_name}", COLOR_SUCCESS)
        time.sleep(0.2)

        saved = False
        for sel in ["#btn_save", "button#btn_save", "input#btn_save",
                    "button:has-text('Save')", "button:has-text('Сохранить')",
                    "button:has-text('保存')", "input[type='submit'][value*='Save']"]:
            try:
                loc = page.locator(sel).first
                if loc.count() > 0 and loc.is_visible():
                    loc.scroll_into_view_if_needed()
                    time.sleep(0.1)
                    loc.click()
                    log_line(f"Clicked Save ({sel})", COLOR_SUCCESS)
                    saved = True
                    break
            except Exception:
                continue
        if not saved:
            log_line("Save button not found", COLOR_ERROR)
            return False

        try:
            page.wait_for_load_state("load", timeout=8000)
        except Exception:
            pass
        time.sleep(0.6)
        try:
            error_box = page.locator("#error_display, .error_ctn").first
            if error_box.count() > 0 and error_box.is_visible():
                err_text = error_box.inner_text().strip()
                if err_text:
                    log_line(f"Rename error from Steam: {truncate_plain(err_text, 120)}",
                             COLOR_ERROR)
                    return False
        except Exception:
            pass

        if open_page_fully(page, f"https://steamcommunity.com/profiles/{steamid64}",
                           timeout=20, scroll=False, retries=2):
            current_name = ""
            try:
                current_name = page.evaluate(
                    "() => (window.g_rgProfileData && window.g_rgProfileData.personaname) || ''"
                )
            except Exception:
                pass
            if current_name == new_name:
                log_line(f"Profile name confirmed: {new_name}", COLOR_SUCCESS, bold=True)
                return True
            log_line(f"Profile name mismatch: expected '{new_name}', got '{current_name}'",
                     COLOR_WARN)
            return False
        log_line("Could not verify profile name (page not loaded)", COLOR_WARN)
        return False
    except Exception as e:
        log_line(f"set_profile_name error: {e}", COLOR_ERROR)
        return False


def is_join_page_loaded(page, timeout=3.0):
    """
    Проверяет, что страница Steam /join реально открылась или хотя бы грузится.
    goto может упасть по таймауту, хотя сайт уже начал отдавать контент —
    тогда страницу надо оставить и продолжить работу.

    True  = страница живая, продолжаем.
    False = грузиться нечего (about:blank / сетевая ошибка), прекращаем попытку.
    """
    deadline = time.time() + timeout
    while True:
        try:
            current = page.url or ""
        except Exception:
            current = ""

        # URL уже /join — всё хорошо
        if "/join" in current:
            return True

        # URL ещё не установился, но страница уже на Steam и что-то на ней есть
        if "steampowered.com" in current:
            try:
                body_len = page.evaluate(
                    "() => document.body ? document.body.innerText.length : 0")
            except Exception:
                body_len = 0
            if body_len > 0:
                return True

        if time.time() >= deadline:
            return False
        time.sleep(0.2)


def try_register(profile_dir):
    """
    Открывает Steam /join напрямую и проходит регистрацию.
    """
    log_line("--- Starting registration (direct) ---", COLOR_WARN, bold=True)
    chrome_proc, cdp_port = launch_chrome_with_cdp(profile_dir)
    try:
        with sync_playwright() as pw:
            try:
                browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{cdp_port}")
            except Exception as e:
                log_line(f"Failed to connect to CDP: {e}", COLOR_ERROR)
                return ('fail', f'cdp: {e}')
            context = browser.contexts[0]
            steam_page = context.new_page()

            t0 = time.time()
            goto_error = None
            try:
                steam_page.goto(STEAM_URL, wait_until="domcontentloaded",
                                timeout=FAST_GOTO)
            except Exception as e:
                goto_error = e
            load_ms = int((time.time() - t0) * 1000)

            # Таймаут/ошибка goto не значит, что страница мёртвая — просто идём дальше.
            if goto_error is not None:
                log_line(f"goto warning ({load_ms}ms): "
                         f"{truncate_plain(str(goto_error), 100)} — continuing",
                         COLOR_WARN)
            else:
                log_line(f"Steam /join is loaded ({load_ms}ms)", COLOR_SUCCESS)

            # Сайт открылся, но поля регистрации могли ещё не подгрузиться.
            # Ждём их, но даже если не дождались — не абортим, едем дальше.
            form_t0 = time.time()
            try:
                steam_page.wait_for_selector(
                    FORM_READY_SELECTOR, timeout=FORM_READY_TIMEOUT, state="attached")
                log_line(f"Registration form is ready "
                         f"({int((time.time() - form_t0) * 1000)}ms)", COLOR_SUCCESS)
            except Exception as e:
                form_ms = int((time.time() - form_t0) * 1000)
                log_line(f"form warning ({form_ms}ms): "
                         f"{truncate_plain(str(e), 80)} — continuing", COLOR_WARN)

            attempt = 0
            captcha_passed = False
            api_user_agent = None

            # Страница загрузилась — повторяем заполнение формы до предела.
            while not captcha_passed and attempt < MAX_FORM_ATTEMPTS:
                attempt += 1

                email_filled = False
                try:
                    email_input = steam_page.wait_for_selector(
                        "#email", timeout=FAST_EMAIL_TIMEOUT, state="visible")
                    if email_input:
                        email_input.fill(EMAIL_ADDRESS)
                        email_filled = True
                        log_line("Email filled")
                except Exception:
                    pass

                if email_filled:
                    try:
                        re_email_input = steam_page.wait_for_selector(
                            "#reenter_email", timeout=3000, state="visible")
                        if re_email_input:
                            re_email_input.fill(EMAIL_ADDRESS)
                            log_line("Email re-entered")
                    except Exception:
                        pass

                try:
                    checkbox = steam_page.locator("#i_agree_check")
                    if not checkbox.is_checked():
                        checkbox.click(force=True)
                except Exception:
                    pass

                sitekey = get_hcaptcha_sitekey(steam_page, timeout=FAST_CAPTCHA_TIMEOUT)
                if not sitekey:
                    time.sleep(0.15)
                    continue

                token, api_user_agent = solve_captcha_only(sitekey, STEAM_URL)
                if not token:
                    log_line("Captcha solve failed, retrying...", COLOR_WARN)
                    time.sleep(0.3)
                    continue

                if api_user_agent:
                    context.set_extra_http_headers({"User-Agent": api_user_agent})

                inject_captcha_token(steam_page, token)
                log_line("Token injected into page...", COLOR_SUCCESS)
                time.sleep(0.2)

                try:
                    continue_btn = steam_page.locator("#createAccountButton, #acceptTerm").first
                    if continue_btn.is_visible():
                        continue_btn.click()
                        log_line("Clicked createAccountButton")
                        time.sleep(1.2)
                except Exception as e:
                    log_line(f"Continue btn error: {e}", COLOR_WARN)

                has_error = False
                for check in range(FAST_ERR_RETRIES):
                    try:
                        error_box = steam_page.locator("#error_display")
                        if error_box.is_visible():
                            err_text = error_box.inner_text().strip()
                            if err_text:
                                log_line(f"Form error: {err_text}", COLOR_ERROR)
                                has_error = True
                                break
                    except Exception:
                        pass
                    time.sleep(FAST_ERR_CHECK)

                if has_error:
                    log_line(f"Attempt failed, retrying ({attempt}/{MAX_FORM_ATTEMPTS})...",
                             COLOR_WARN)
                else:
                    captcha_passed = True
                    break

            if not captcha_passed:
                try:
                    browser.close()
                except Exception:
                    pass
                return ('fail', f'form retries exhausted ({attempt}/{MAX_FORM_ATTEMPTS})')

            # Ждём письмо с подтверждением. Если за CONFIRM_MAIL_TIMEOUT
            # секунд его нет — закрываем Steam, перезапускаем Chrome и
            # проходим регистрацию заново.
            confirm_link = None
            for mail_try in range(1, CONFIRM_MAIL_RETRIES + 1):
                log_line(f"Waiting for Steam confirmation email in Gmail "
                         f"({mail_try}/{CONFIRM_MAIL_RETRIES}, "
                         f"{CONFIRM_MAIL_TIMEOUT}s)...", COLOR_WARN)
                confirm_link = get_steam_confirm_link(
                    timeout=CONFIRM_MAIL_TIMEOUT, interval=1)
                if confirm_link:
                    break

                if mail_try < CONFIRM_MAIL_RETRIES:
                    log_line(f"No confirmation link in {CONFIRM_MAIL_TIMEOUT}s — "
                             f"restarting Chrome and retrying registration",
                             COLOR_ERROR)
                    try:
                        steam_page.goto(STEAM_URL, wait_until="domcontentloaded",
                                        timeout=FAST_GOTO)
                    except Exception as e:
                        log_line(f"Reopen Steam failed: {truncate_plain(str(e), 80)}",
                                 COLOR_ERROR)
                    time.sleep(0.5)
                else:
                    log_line(f"No confirmation link after "
                             f"{CONFIRM_MAIL_RETRIES} tries — giving up on this attempt",
                             COLOR_ERROR)

            if confirm_link:
                log_line(f"Opening confirm link in NEW tab: {confirm_link[:80]}...")
                confirm_page = context.new_page()
                try:
                    if open_page_fully(confirm_page, confirm_link, timeout=20,
                                       scroll=False, retries=2):
                        log_line(f"Confirm page URL: {confirm_page.url}", COLOR_SUCCESS)
                    else:
                        log_line("Confirm page did not load properly", COLOR_ERROR)
                except Exception as e:
                    log_line(f"Failed to open confirm link: {e}", COLOR_ERROR)
                finally:
                    try:
                        confirm_page.close()
                        log_line("Confirm tab closed", COLOR_SUCCESS)
                    except Exception as e:
                        log_line(f"Failed to close confirm tab: {e}", COLOR_WARN)

                steam_page.bring_to_front()
                log_line("Waiting for old tab to auto-update...")
                log_line(f"steam_page URL: {steam_page.url}")

                time.sleep(0.5)
                log_line("Looking for continue button (继续/Продолжить/Continue)...")
                clicked = click_visible_button_by_text(steam_page, [
                    "继续", "Продолжить", "Continue"
                ])
                if clicked:
                    log_line("Continue clicked, waiting for form...", COLOR_SUCCESS)
                    time.sleep(0.5)

                accountname_found = False
                try:
                    steam_page.wait_for_selector(
                        "#accountname",
                        timeout=15000, state="visible"
                    )
                    accountname_found = True
                    log_line("#accountname появился", COLOR_SUCCESS)
                except Exception as e:
                    log_line(f"#accountname не появился за 15с: {e}", COLOR_ERROR)

                if not accountname_found:
                    log_line("Account form not found", COLOR_ERROR)
                    try:
                        browser.close()
                    except Exception:
                        pass
                    return ('fail', 'no accountname')

                steam_page.bring_to_front()
                account_created = False
                steam_login = ""
                steam_password = ""
                max_attempts = 5
                for attempt in range(1, max_attempts + 1):
                    steam_login = random_login(random.randint(8, 16))
                    steam_password = gen_password(random.randint(12, 20))
                    try:
                        steam_page.wait_for_selector("#accountname", timeout=15000, state="visible")
                        time.sleep(0.15)
                        steam_page.fill("#accountname", "")
                        steam_page.fill("#password", "")
                        steam_page.fill("#reenter_password", "")
                        log_line("Name Logging...")
                        steam_page.fill("#accountname", steam_login)

                        log_line("Password Logging...")
                        for char in steam_password:
                            steam_page.type("#password", char)
                            time.sleep(0.015)

                        log_line("Password Repeating...")
                        for char in steam_password:
                            steam_page.type("#reenter_password", char)
                            time.sleep(0.015)

                        time.sleep(0.3)
                        create_btn = steam_page.locator("#createAccountButton, #acceptTerm").first
                        if create_btn.is_visible():
                            create_btn.click()
                            log_line("Account created", COLOR_SUCCESS)
                            time.sleep(2)
                        has_error = False
                        error_text = ""
                        for check in range(FAST_ERR_RETRIES):
                            try:
                                error_box = steam_page.locator("#error_display, .newlogin_content_error_text")
                                if error_box.is_visible():
                                    error_text = error_box.inner_text().strip()
                                    if error_text:
                                        has_error = True
                                        break
                            except Exception:
                                pass
                            time.sleep(FAST_ERR_CHECK)
                        if has_error:
                            log_line(f"Attempt {attempt} error: {error_text}", COLOR_ERROR)
                            time.sleep(0.3)
                            continue
                        else:
                            account_created = True
                            log_line("Registration Complete!", COLOR_SUCCESS, bold=True)
                            break
                    except Exception as e:
                        log_line(f"Attempt {attempt} crashed: {e}", COLOR_ERROR)
                        if attempt < max_attempts:
                            time.sleep(0.3)

                if not account_created:
                    log_line("Account NOT created", COLOR_ERROR)
                    try:
                        browser.close()
                    except Exception:
                        pass
                    return ('fail', 'not created')

                steamid64 = ""
                try:
                    log_line("Getting SteamID64 from /my/profile...")
                    steamid64 = get_steamid64_from_page(steam_page, timeout=15)
                    if steamid64:
                        log_line(f"SteamID64: {steamid64}", COLOR_SUCCESS, bold=True)
                    else:
                        log_line("SteamID64 not found", COLOR_ERROR)
                except Exception as e:
                    log_line(f"SteamID64 error: {e}", COLOR_ERROR)

                if CUSTOM_NAME and steamid64:
                    log_line(f"Setting custom name: {CUSTOM_NAME}")
                    try:
                        set_profile_name(steam_page, steamid64, CUSTOM_NAME, timeout=15)
                    except Exception as e:
                        log_line(f"set_profile_name error: {e}", COLOR_ERROR)
                elif not CUSTOM_NAME:
                    log_line("Custom name not set — skipping rename", COLOR_WARN)

                avatar_image = pick_avatar_file() if AVATAR_ENABLED else None
                if not AVATAR_ENABLED:
                    log_line("Avatar upload is off in Setting — skipping", COLOR_WARN)
                elif not steamid64:
                    log_line("No SteamID64 — skipping avatar", COLOR_WARN)
                elif avatar_image:
                    log_line(f"Setting avatar from {AVATAR_DIR.name}: {avatar_image.name}")
                    try:
                        if not set_profile_avatar(steam_page, steamid64, avatar_image):
                            log_line("Avatar upload failed — continuing without it",
                                     COLOR_WARN)
                    except Exception as e:
                        log_line(f"set_profile_avatar error: {e}", COLOR_ERROR)
                else:
                    log_line(f"No image in {AVATAR_DIR.name} folder — skipping avatar "
                             f"(supported: {', '.join(AVATAR_EXTENSIONS)})", COLOR_WARN)

            else:
                # Ссылка так и не пришла за все попытки. Аккаунт на Steam
                # без подтверждения не создан — закрываем браузер и
                # начинаем заново (внешний цикл перезапустит Chrome).
                log_line(f"Registration aborted: no confirmation link after "
                         f"{CONFIRM_MAIL_RETRIES} tries", COLOR_ERROR)
                try:
                    browser.close()
                except Exception:
                    pass
                return ('fail', 'no confirmation link')

            date_str = get_date_string()
            profile_url = (f"https://steamcommunity.com/profiles/{steamid64}"
                           if steamid64 else "")
            line = (f"{steam_login}|{steam_password}|{EMAIL_ADDRESS} "
                    f"// SteamID: {steamid64 or 'unknown'} "
                    f"// Profile: {profile_url} "
                    f"// Date: {date_str}\n")
            try:
                with open(ACCOUNTS_FILE, "a", encoding="utf-8") as f:
                    f.write(line)
                log_line("Account saved to account.txt", COLOR_SUCCESS)
                log_line(f"  {line.strip()}", COLOR_DIM)
            except Exception as e:
                log_line(f"Save error: {e}", COLOR_ERROR)

            send_to_discord(steam_login, steam_password, EMAIL_ADDRESS, steamid64)

            try:
                browser.close()
            except Exception:
                pass
            return ('success', None)
    finally:
        kill_chrome_proc(chrome_proc, profile_dir)


def purge_old_profiles():
    PROFILE_BASE_DIR.mkdir(parents=True, exist_ok=True)
    extra = []
    for entry in PROFILE_BASE_DIR.iterdir():
        if not entry.is_dir():
            continue
        if entry.name == PROFILE_NAME:
            continue
        extra.append(entry)
    if not extra:
        return
    kill_chrome_by_profile(PROFILE_BASE_DIR)
    for entry in extra:
        remove_profile_dir(entry)
    log_line(f"Cleaned old profiles: {len(extra)}", COLOR_WARN)


def drop_profile():
    global PROFILE_DIR
    if PROFILE_DIR is None:
        return
    kill_chrome_by_profile(PROFILE_DIR)
    remove_profile_dir(PROFILE_DIR)
    PROFILE_DIR = None


def register_one_account(account_number):
    global PROFILE_DIR
    profile_dir = PROFILE_BASE_DIR / PROFILE_NAME

    # Чистый профиль перед каждой попыткой — без следов прошлых заходов.
    PROFILE_DIR = profile_dir
    drop_profile()
    PROFILE_DIR = profile_dir

    log("--- Starting registration (direct connection) ---", "warning")
    result, reason = try_register(profile_dir)
    if result == 'success':
        log("SUCCESS!", "success")
        drop_profile()
        return True

    log(f"Registration failed: {reason}", "error")
    drop_profile()
    return False


def generate_accounts(total):
    if NONECAP_API_KEY == "":
        print_result(False, "NoneCap API Key not set!")
        write("  " + color("Set it in Settings first.", COLOR_MUTED) + "\n")
        if RESULT_SCREEN_DELAY > 0:
            time.sleep(RESULT_SCREEN_DELAY)
        return

    created = 0
    for number in range(1, total + 1):
        clear_screen()
        restore_console_font()
        print_banner()
        log(f"Generating {total} account(s)...", "warning")
        if register_one_account(number):
            created += 1
        if number < total:
            time.sleep(ACCOUNT_GAP)

    write("\n")
    print_result(True, "Generation finished",
                 detail=f"Created {created} of {total} account(s)")
    # Не ждём Enter — просто держим результат на экране и возвращаемся в меню
    if RESULT_SCREEN_DELAY > 0:
        log(f"Returning to menu in {RESULT_SCREEN_DELAY}s", "info")
        time.sleep(RESULT_SCREEN_DELAY)


def _edit_name_setting(title, current_value):
    print_box(title, current_value if current_value else "[NOT SET]", COLOR_VALUE)
    time.sleep(1.0)
    value = prompt_line(f"{title} (a-z A-Z 0-9 _, 3-32 chars, empty to clear): ")
    value = value.strip()
    if value == "":
        if current_value:
            return "", True
        log("and so not set", "warning")
        return "", False
    if re.fullmatch(r"[A-Za-z0-9_]{3,32}", value):
        return value, True
    log("Name must be 3-32 chars of A-Za-z0-9_", "error")
    return current_value, False


def show_avatar_setting():
    global AVATAR_ENABLED
    ensure_avatar_dir()
    image = pick_avatar_file()

    clear_screen()
    print_banner()
    for number, label in [
        (1, f"Use avatar from {AVATAR_DIR.name} folder"),
        (2, "Show all files"),
        (3, "Open Avatar folder"),
        (4, f"Avatar: {'ON' if AVATAR_ENABLED else 'OFF'}"),
        (0, "Back to Main Menu"),
    ]:
        write("\n")
        print_menu_item(number, label)
    write("\n")

    if image:
        size_kb = max(1, image.stat().st_size // 1024)
        print_box("Avatar file", f"{image.name} ({size_kb} KB) — will be used", LOG_SUCCESS)
    else:
        print_box("Avatar folder", f"{AVATAR_DIR.name} is empty — add .png or .jpg",
                  LOG_WARNING)

    choice = prompt_line("Select option: ").strip()
    if choice == "1":
        if image is None:
            print_result(False, f"No images in {AVATAR_DIR.name} — add a file first")
        else:
            if not AVATAR_ENABLED:
                AVATAR_ENABLED = True
                save_settings()
            size_kb = max(1, image.stat().st_size // 1024)
            print_result(True, f"Avatar: ON — will use {image.name} ({size_kb} KB)")
        time.sleep(1.5)
    elif choice == "2":
        files = avatar_files()
        if not files:
            log(f"No images in {AVATAR_DIR.name}", "warning")
        else:
            print_result(True, f"Found {len(files)} file(s) in {AVATAR_DIR}")
            for i, path in enumerate(files, 1):
                size_kb = max(1, path.stat().st_size // 1024)
                print_box(f"  {i}.", f"{path.name} ({size_kb} KB)")
            print_box("Selected", files[0].name, LOG_SUCCESS)
        time.sleep(2)
    elif choice == "3":
        try:
            os.startfile(str(AVATAR_DIR))
            print_result(True, f"Opened {AVATAR_DIR}")
        except Exception as e:
            print_box("Folder", f"{AVATAR_DIR} ({e})", LOG_WARNING)
        time.sleep(1.0)
    elif choice == "4":
        if not AVATAR_ENABLED and image is None:
            print_result(False, f"Add an image to {AVATAR_DIR.name} first")
        else:
            AVATAR_ENABLED = not AVATAR_ENABLED
            save_settings()
            print_result(True, f"Avatar: {'ON' if AVATAR_ENABLED else 'OFF'}")
        time.sleep(1.0)
    elif choice not in ("0", "5"):
        print_result(False, "Invalid option")
        time.sleep(0.8)


def account_total_hint(count):
    """'1 аккаунт', '2 аккаунта', '5 аккаунтов' — по-русски с учётом склонения."""
    count = max(0, int(count))
    if count % 10 == 1 and count % 100 != 11:
        word = "аккаунт"
    elif count % 10 in (2, 3, 4) and count % 100 not in (12, 13, 14):
        word = "аккаунта"
    else:
        word = "аккаунтов"
    return f"{count} {word}"


def show_proxy_setting():
    global PROXY_ENABLED, PROXY_VALUE
    while True:
        clear_screen()
        print_banner()
        options = [
            (1, f"Proxy: {'ON' if PROXY_ENABLED else 'OFF'}"),
            (2, "Set proxy: " + summarize_proxy(PROXY_VALUE)),
            (3, "Test proxy"),
            (4, "Clear proxy"),
            (0, "Back to Settings"),
        ]
        for number, label in options:
            write("\n")
            print_menu_item(number, label)
        write("\n")

        candidates = proxy_candidates()
        if PROXY_VALUE and not candidates:
            print_box("Proxy", "строка есть, но формат невалидный", LOG_WARNING)
        elif candidates:
            print_box("Loaded", f"{len(candidates)} proxy in list")
        else:
            print_box("Proxy", "не задан — браузер пойдёт напрямую", LOG_WARNING)
        write("\n")

        choice = prompt_line("Select option: ").strip()
        if choice == "0":
            return

        if choice == "1":
            if not PROXY_VALUE:
                print_result(False, "Сначала задай прокси (пункт 2)")
            else:
                PROXY_ENABLED = not PROXY_ENABLED
                save_settings()
                print_result(True, f"Proxy: {'ON' if PROXY_ENABLED else 'OFF'}")
            time.sleep(1.0)
        elif choice == "2":
            write("\n")
            print_box("Formats", "ip:port | http://ip:port | https://ip:port")
            print_box("", "socks4://ip:port | socks5://ip:port | socks5h://ip:port")
            print_box("", "user:pass@ip:port — тоже понимает")
            print_box("List", "несколько через запятую = рандом на аккаунт")
            write("\n")
            value = prompt_line("Enter proxy (empty to cancel): ").strip()
            if value == "":
                continue
            chunks = [c for c in re.split(r"[,;\r\n]+", value) if c.strip()]
            bad = [c for c in chunks if not parse_proxy(c)]
            if bad:
                print_result(False, f"Невалидный прокси: {bad[0]}")
                print_box("Hint", "формат: scheme://user:pass@host:port")
                time.sleep(1.8)
                continue
            PROXY_VALUE = ",".join(chunks)
            PROXY_ENABLED = True
            save_settings()
            print_result(True, f"Proxy saved: {summarize_proxy(PROXY_VALUE)}")
            time.sleep(1.2)
        elif choice == "3":
            candidates = proxy_candidates()
            if not candidates:
                print_result(False, "Нет валидного прокси для теста")
                time.sleep(1.2)
                continue
            for parsed in candidates:
                log_line(f"Testing {parsed['display']} ...", COLOR_DIM)
                ok, info = check_proxy(parsed)
                print_result(ok, f"{parsed['display']} — {'OK' if ok else 'FAIL'}", detail=info)
            write("\n")
            wait_for_enter()
        elif choice == "4":
            PROXY_VALUE = ""
            PROXY_ENABLED = False
            save_settings()
            print_result(True, "Proxy cleared")
            time.sleep(1.0)
        else:
            print_result(False, "Invalid option")
            time.sleep(0.8)


def show_settings():
    global HEADLESS_MODE, ACCOUNTS_TOTAL, NONECAP_API_KEY, DISCORD_WEBHOOK, CUSTOM_NAME
    while True:
        clear_screen()
        print_banner()

        proxy_label = "OFF"
        if PROXY_ENABLED:
            cands = proxy_candidates()
            if not cands:
                proxy_label = "ON [NOT SET]"
            elif len(cands) > 1:
                proxy_label = f"ON ({len(cands)} in list)"
            else:
                proxy_label = f"ON {cands[0]['display']}"
        options = [
            (1, f"Headless Mode: {'ON' if HEADLESS_MODE else 'OFF'}"),
            (2, f"Account Total: {ACCOUNTS_TOTAL}"),
            (3, "NoneCap API Key: " + ("[NOT SET]" if not NONECAP_API_KEY else "[SET]")),
            (4, "Discord Webhook: " + ("[NOT SET]" if not DISCORD_WEBHOOK else "[SET]")),
            (5, "Custom Name: " + (CUSTOM_NAME if CUSTOM_NAME else "[NOT SET]")),
            (6, f"Avatar: {'ON' if AVATAR_ENABLED else 'OFF'}"),
            (7, "Proxy: " + proxy_label),
            (0, "Back to Main Menu"),
        ]
        for number, label in options:
            print_menu_item(number, label)
        write("\n")

        choice = prompt_line("Select option: ").strip()
        if choice == "0":
            return

        if choice == "1":
            HEADLESS_MODE = not HEADLESS_MODE
            save_settings()
            print_result(True, f"Headless mode: {'ON' if HEADLESS_MODE else 'OFF'}")
            time.sleep(1.0)
        elif choice == "2":
            value = prompt_line("Enter number of accounts to generate: ").strip()
            if value.isdigit() and int(value) > 0:
                ACCOUNTS_TOTAL = int(value)
                save_settings()
                print_result(True, f"Будет создано "
                                   f"{account_total_hint(ACCOUNTS_TOTAL)}")
            else:
                print_result(False, "Value must be positive")
            time.sleep(1.2)
        elif choice == "3":
            print_box("NoneCap API Key", "[NOT SET]" if not NONECAP_API_KEY else "[SET]")
            time.sleep(1.2)
            value = prompt_line("Enter NoneCap API Key (empty to clear): ").strip()
            if value == "":
                NONECAP_API_KEY = ""
                save_settings()
                print_result(True, "API Key cleared")
            elif value.startswith("nc_live_"):
                NONECAP_API_KEY = value
                save_settings()
                print_result(True, "API Key saved")
            else:
                print_result(False, "Invalid key format (must start with nc_live_)")
            time.sleep(1.2)
        elif choice == "4":
            print_box("Discord Webhook", DISCORD_WEBHOOK or "[NOT SET]")
            time.sleep(1.2)
            value = prompt_line("Enter Discord Webhook URL (empty to clear): ").strip()
            if value == "":
                DISCORD_WEBHOOK = ""
                save_settings()
                print_result(True, "Webhook cleared")
            elif (value.startswith("https://discord.com/api/webhooks/") or
                  value.startswith("https://discordapp.com/api/webhooks/")):
                DISCORD_WEBHOOK = value
                save_settings()
                print_result(True, "Webhook saved")
            else:
                print_result(False, "Invalid Webhook format")
            time.sleep(1.2)
        elif choice == "5":
            value, changed = _edit_name_setting("Custom Name", CUSTOM_NAME)
            if changed:
                CUSTOM_NAME = value
                save_settings()
                print_result(True, "Custom name cleared" if not value
                             else f"Custom name saved: {value}")
            time.sleep(1.2)
        elif choice == "6":
            show_avatar_setting()
        elif choice == "7":
            show_proxy_setting()
        else:
            print_result(False, "Invalid option")
            time.sleep(1.0)


def show_menu():
    while True:
        clear_screen()
        print_banner()
        print_main_menu()
        write("\n")
        try:
            choice = prompt_line("Select option: ").strip()
        except (EOFError, KeyboardInterrupt):
            return "exit"
        if choice in ("", "4", "q", "Q", "exit"):
            return "back"
        elif choice == "1":
            return "generate"
        elif choice == "2":
            show_settings()
        elif choice == "3":
            return "inbox"
        else:
            print_result(False, "Invalid option")
            time.sleep(1.0)


def main():
    capture_console_font()
    enable_unicode_output()
    load_settings()
    if "--selftest" in sys.argv:
        problems = inbox_self_test(verbose=True)
        raise SystemExit(1 if problems else 0)

    resize_console(CONSOLE_WIDTH, CONSOLE_HEIGHT)
    hide_cursor()

    PROFILE_BASE_DIR.mkdir(parents=True, exist_ok=True)
    purge_old_profiles()
    ensure_avatar_dir()

    try:
        while True:
            action = show_menu()
            if action == "generate":
                try:
                    generate_accounts(ACCOUNTS_TOTAL)
                except KeyboardInterrupt:
                    raise
                except Exception:
                    handle_crash()
                    return
            elif action == "back":
                continue
            elif action == "exit":
                log("Exiting...", "info")
                return
            elif action == "inbox":
                try:
                    inbox_watch_loop()
                except KeyboardInterrupt:
                    ib_clear_live_status()
                    show_cursor()
                    print()
                    log("Inbox stopped (Ctrl+C)", "warning")
                except Exception as e:
                    ib_clear_live_status()
                    show_cursor()
                    print()
                    print_result(False, f"Inbox error: {e}")
                    time.sleep(2)
    finally:
        show_cursor()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        show_cursor()
    except SystemExit:
        raise
    except Exception:
        handle_crash()									