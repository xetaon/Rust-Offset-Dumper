import sqlite3, os

p = os.path.expanduser('~/.local/share/opencode/opencode.db')
c = sqlite3.connect('file:' + p.replace('\\', '/') + '?mode=ro', uri=True)
for (name,) in c.execute("select name from sqlite_master where type='table' order by name").fetchall():
    sql = c.execute("select sql from sqlite_master where name=?", (name,)).fetchone()[0]
    print('---', name)
    print(sql)
    print('FK:', c.execute('pragma foreign_key_list("%s")' % name).fetchall())
print('--- sample session')
for r in c.execute('select id, project_id, parent_id, title from session_v2 limit 3'):
    print(r)
print('--- distinct project_ids', c.execute('select count(distinct project_id) from session_v2').fetchone())
print('--- event sample', c.execute('select aggregate_id, type from event limit 3').fetchall())
