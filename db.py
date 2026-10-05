"""Tiny SQLite layer for price history."""
import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.getenv("DB_PATH", "prices.db")


def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute(
        """CREATE TABLE IF NOT EXISTS prices (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               url TEXT NOT NULL,
               name TEXT,
               price REAL NOT NULL,
               ts TEXT NOT NULL
           )"""
    )
    return c


def last_price(url):
    with conn() as c:
        row = c.execute(
            "SELECT price FROM prices WHERE url = ? ORDER BY ts DESC, id DESC LIMIT 1", (url,)
        ).fetchone()
    return row["price"] if row else None


def add_price(url, name, price, ts=None):
    ts = ts or datetime.now(timezone.utc).isoformat(timespec="seconds")
    with conn() as c:
        c.execute(
            "INSERT INTO prices (url, name, price, ts) VALUES (?, ?, ?, ?)",
            (url, name, price, ts),
        )


def history():
    """Return {url: {"name": str, "points": [{"t": iso, "p": float}, ...]}}"""
    out = {}
    with conn() as c:
        rows = c.execute("SELECT url, name, price, ts FROM prices ORDER BY ts, id").fetchall()
    for r in rows:
        item = out.setdefault(r["url"], {"name": r["name"], "points": []})
        item["name"] = r["name"] or item["name"]
        item["points"].append({"t": r["ts"], "p": r["price"]})
    return out
