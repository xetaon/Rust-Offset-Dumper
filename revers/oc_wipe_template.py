import os
import sqlite3
import sys

db = os.path.join(
    os.environ.get("USERPROFILE") or os.path.expanduser("~"),
    ".local", "share", "opencode", "opencode.db",
)

if not os.path.exists(db):
    print("Database not found:", db)
    sys.exit(2)

try:
    conn = sqlite3.connect(db, timeout=30)
    conn.execute("PRAGMA foreign_keys=ON")
    ids = [row[0] for row in conn.execute("SELECT id FROM session_v2")]
    conn.executemany(
        "DELETE FROM event_sequence WHERE aggregate_id=?",
        [(sid,) for sid in ids],
    )
    conn.execute("DELETE FROM session_v2")
    conn.execute("DELETE FROM blob WHERE hash NOT IN (SELECT hash FROM blob_ref)")
    conn.commit()
    left = conn.execute("SELECT count(*) FROM session_v2").fetchone()[0]
    conn.close()
except Exception as exc:
    print("ERROR:", exc)
    sys.exit(1)

print("Sessions deleted:", len(ids))
print("Sessions remaining:", left)
sys.exit(0 if left == 0 else 3)
