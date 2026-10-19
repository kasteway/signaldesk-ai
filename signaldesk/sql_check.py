"""Load the checked extract into SQLite and verify headline SQL aggregates."""
from __future__ import annotations
import sqlite3
from .core import load_rows

def run() -> list[tuple]:
    rows = load_rows()
    with sqlite3.connect(":memory:") as db:
        db.execute("CREATE TABLE complaints (complaint_id TEXT PRIMARY KEY, date_received TEXT, issue TEXT, sub_product TEXT)")
        db.executemany("INSERT INTO complaints VALUES (?,?,?,?)", [(r['complaint_id'],r['date_received'],r['issue'],r['sub_product']) for r in rows])
        result = db.execute("SELECT issue, COUNT(*) AS complaints FROM complaints GROUP BY issue ORDER BY complaints DESC").fetchall()
    return result

if __name__ == '__main__':
    for issue, count in run()[:10]: print(f"{count:>5}  {issue}")
