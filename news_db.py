import os
import sqlite3
from typing import List, Dict, Optional

DATABASE_URL = os.getenv("DATABASE_URL")  # появится на Railway после добавления Postgres

# ---------- SQLITE (локально) ----------
SQLITE_PATH = os.getenv("SQLITE_PATH", "news.db")


def _sqlite_conn():
    return sqlite3.connect(SQLITE_PATH)


def _sqlite_init():
    con = _sqlite_conn()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            date_text TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    con.commit()
    con.close()


def _sqlite_add_news(title: str, description: str, date_text: str) -> int:
    con = _sqlite_conn()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO news (title, description, date_text) VALUES (?, ?, ?)",
        (title, description, date_text),
    )
    con.commit()
    news_id = cur.lastrowid
    con.close()
    return int(news_id)


def _sqlite_list_news(limit: int = 50) -> List[Dict]:
    con = _sqlite_conn()
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(
        "SELECT id, title, description, date_text, created_at FROM news ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = cur.fetchall()
    con.close()
    return [dict(r) for r in rows]


# ---------- POSTGRES (Railway) ----------
def _pg_conn():
    # psycopg v3
    import psycopg
    return psycopg.connect(DATABASE_URL)


def _pg_init():
    con = _pg_conn()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            date_text TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)
    con.commit()
    cur.close()
    con.close()


def _pg_add_news(title: str, description: str, date_text: str) -> int:
    con = _pg_conn()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO news (title, description, date_text) VALUES (%s, %s, %s) RETURNING id",
        (title, description, date_text),
    )
    news_id = cur.fetchone()[0]
    con.commit()
    cur.close()
    con.close()
    return int(news_id)


def _pg_list_news(limit: int = 50) -> List[Dict]:
    con = _pg_conn()
    cur = con.cursor()
    cur.execute(
        "SELECT id, title, description, date_text, created_at FROM news ORDER BY id DESC LIMIT %s",
        (limit,),
    )
    rows = cur.fetchall()
    cur.close()
    con.close()
    return [
        {
            "id": r[0],
            "title": r[1],
            "description": r[2],
            "date_text": r[3],
            "created_at": str(r[4]),
        }
        for r in rows
    ]


# ---------- Публичные функции ----------
def init_db():
    if DATABASE_URL:
        _pg_init()
    else:
        _sqlite_init()


def add_news(title: str, description: str, date_text: str) -> int:
    if DATABASE_URL:
        return _pg_add_news(title, description, date_text)
    return _sqlite_add_news(title, description, date_text)


def list_news(limit: int = 50) -> List[Dict]:
    if DATABASE_URL:
        return _pg_list_news(limit=limit)
    return _sqlite_list_news(limit=limit)