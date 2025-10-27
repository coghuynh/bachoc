# db.py
import sqlite3
from contextlib import contextmanager

class DB:
    def __init__(self, path: str = "kg.db"):
        self.conn = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.conn.execute("PRAGMA journal_mode = WAL;")  # tốt cho concurrency đọc/ghi nhẹ
        self.conn.execute("PRAGMA synchronous = NORMAL;")

    def execute(self, sql: str, params: tuple = ()):
        cur = self.conn.execute(sql, params)
        self.conn.commit()
        return cur

    def query(self, sql: str, params: tuple = ()):
        cur = self.conn.execute(sql, params)
        return cur.fetchall()

    @contextmanager
    def transaction(self):
        try:
            self.conn.execute("BEGIN;")
            yield
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def close(self):
        self.conn.close()