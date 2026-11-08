import sqlite3, os

p = os.path.expanduser('~/.local/share/opencode/opencode.db')
c = sqlite3.connect('file:' + p.replace('\\', '/') + '?mode=ro', uri=True)
print('TABLES:')
for row in c.execute("select name from sqlite_master where type='table' order by name"):
    print(' ', row[0])
print()
for (name,) in c.execute("select name from sqlite_master where type='table' order by name").fetchall():
    try:
        n = c.execute('select count(*) from "%s"' % name).fetchone()[0]
        cols = [r[1] for r in c.execute('pragma table_info("%s")' % name)]
        print(name, n, cols)
    except Exception as e:
        print(name, 'ERR', e)
