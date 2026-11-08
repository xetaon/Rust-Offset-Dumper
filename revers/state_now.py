import sqlite3, os

p = os.path.expanduser('~/.local/share/opencode/opencode.db')
c = sqlite3.connect('file:' + p.replace('\\', '/') + '?mode=ro', uri=True)
print('total sessions:', c.execute('select count(*) from session_v2').fetchone()[0])
print('top-level:', c.execute('select count(*) from session_v2 where parent_id is null').fetchone()[0])
print('empty/New session titles:')
for r in c.execute("select id, project_id, title, time_created, time_updated, time_archived from session_v2 where title is null or title='' or title='New session' order by time_updated desc limit 20"):
    print(' ', r)
print('projects with sessions:')
for r in c.execute('select project_id, count(*) from session_v2 group by project_id order by count(*) desc limit 10'):
    print(' ', r)
print('sample recent sessions:')
for r in c.execute('select id, title, project_id, time_updated from session_v2 order by time_updated desc limit 10'):
    print(' ', r)
