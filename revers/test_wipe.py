import sqlite3, os

p = os.path.join(os.environ['TEMP'], 'opencode', 'dbcopy', 'opencode.db')

def counts(c):
    tables = ['session_v2','session_message','blob_ref','blob','instruction_state','instruction_entry','session_inbox','event','event_sequence']
    return {t: c.execute('select count(*) from "%s"' % t).fetchone()[0] for t in tables}

c = sqlite3.connect(p)
print('before:', counts(c))
c.execute('PRAGMA foreign_keys=ON')
ids = [r[0] for r in c.execute('SELECT id FROM session_v2')]
c.executemany('DELETE FROM event_sequence WHERE aggregate_id=?', [(i,) for i in ids])
c.execute('DELETE FROM session_v2')
c.execute('DELETE FROM blob WHERE hash NOT IN (SELECT hash FROM blob_ref)')
c.commit()
print('deleted sessions:', len(ids))
print('after:', counts(c))
c.close()
