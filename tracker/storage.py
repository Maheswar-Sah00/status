"""SQLite history: remembers what was already seen so 'NEW TODAY' is accurate."""
import hashlib
import re
import sqlite3
from datetime import date

COLUMNS = ["type", "title", "org", "location", "deadline", "posted", "pay",
           "source", "link", "notes", "score"]


def key(o):
    """Same role cross-posted on several boards should collapse to one row."""
    t = re.sub(r"[^a-z0-9]", "", o["title"].lower())
    g = re.sub(r"[^a-z0-9]", "", o["org"].lower())
    basis = f"{o['type']}|{t}|{g}" if g else (o["link"] or t)
    return hashlib.sha1(basis.encode()).hexdigest()[:16]


def connect(path):
    db = sqlite3.connect(path)
    db.execute(f"""CREATE TABLE IF NOT EXISTS opp (
        id TEXT PRIMARY KEY, {", ".join(c + " TEXT" for c in COLUMNS)},
        first_seen TEXT, last_seen TEXT)""")
    return db


def upsert(db, rows):
    today = date.today().isoformat()
    new = 0
    for o in rows:
        k = key(o)
        vals = [str(o.get(c, "")) for c in COLUMNS]
        cur = db.execute(f"UPDATE opp SET {', '.join(c + '=?' for c in COLUMNS)}, last_seen=? WHERE id=?",
                         vals + [today, k])
        if cur.rowcount == 0:
            db.execute(f"INSERT INTO opp VALUES (?, {', '.join('?' * len(COLUMNS))}, ?, ?)",
                       [k] + vals + [today, today])
            new += 1
    db.commit()
    return new


def active(db, max_age_days=45):
    """Rows seen in the latest run window (still listed somewhere)."""
    cur = db.execute("""SELECT * FROM opp WHERE last_seen >= date('now', ?)
                        ORDER BY first_seen DESC, CAST(score AS INT) DESC""", (f"-{max_age_days} days",))
    names = [d[0] for d in cur.description]
    return [dict(zip(names, r)) for r in cur.fetchall()]
