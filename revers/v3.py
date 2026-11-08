import io
p = r"C:\Users\SystemX\Desktop\SteamAccGen\SteamAccGen.py"
s = io.open(p, encoding="utf-8").read()
for needle in ["Не российские, отброшены: ", "Ни одного российского прокси",
               "RU only: в списке нет российских прокси",
               "RU filter: ", "(RU only)"]:
    print(needle, "->", needle in s)
