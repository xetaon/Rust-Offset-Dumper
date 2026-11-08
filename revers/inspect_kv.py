import sqlite3, os

p = os.path.expanduser('~/.local/share/opencode/opencode.db')
c = sqlite3.connect('file:' + p.replace('\\', '/') + '?mode=ro', uri=True)
print('KV:')
for k, v in c.execute('select key, substr(value,1,200) from kv'):
    print(' ', k, '=', v)
print('projects:')
for r in c.execute('select id, worktree, name from project limit 5'):
    print(' ', r)
print('event_sequence owners sample:', c.execute('select * from event_sequence limit 5').fetchall())
print('session dirs sample:', c.execute('select id, directory, path from session_v2 limit 5').fetchall())
