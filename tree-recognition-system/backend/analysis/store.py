"""Persist JSON reports, not raw uploads or provider credentials."""
import json
from contextlib import closing
from pathlib import Path
import sqlite3


class AnalysisStore:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS analysis_reports (
                id TEXT PRIMARY KEY, created_at TEXT NOT NULL, report TEXT NOT NULL
            )""")

    def save(self, report):
        payload = json.dumps(report, ensure_ascii=False, allow_nan=False)
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute("INSERT INTO analysis_reports VALUES (?, ?, ?)",
                               (report["id"], report["created_at"], payload))

    def get(self, report_id):
        with closing(sqlite3.connect(self.path)) as connection, connection:
            row = connection.execute("SELECT report FROM analysis_reports WHERE id = ?", (report_id,)).fetchone()
        return json.loads(row[0]) if row else None
