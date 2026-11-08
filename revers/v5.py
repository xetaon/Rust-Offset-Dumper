import io
p = r"C:\Users\SystemX\Desktop\SteamAccGen\SteamAccGen.py"
s = io.open(p, encoding="utf-8").read()
mine = ["parse_proxy", "ProxyRelay", "pick_proxy", "refresh_auto_proxies",
        "fetch_country_codes", "proxy_country", "is_russian_proxy",
        "_probe_proxy", "_ip_from_info", "show_proxy_setting", "mask_proxy",
        "summarize_proxy", "check_proxy", "proxy_candidates", "_fetch_one_source",
        "fetch_proxies_online", "PROXY_ENABLED", "PROXY_VALUE", "RU_ONLY",
        "AUTO_PROXIES", "ThreadPoolExecutor", "import ssl", "import select"]
for m in mine:
    if m in s:
        print("STILL PRESENT:", m)
print("scan done")
# verify key original functions intact
for f in ["launch_chrome_with_cdp", "kill_chrome_proc", "show_settings",
          "generate_accounts", "register_one_account", "load_settings",
          "save_settings", "try_register", "router_cycle", "shutdown_watchdog"]:
    print(f, "def" and (f"def {f}(" in s))
