# -*- coding: utf-8 -*-
import aiosqlite
from typing import Optional, List

_DB: Optional[aiosqlite.Connection] = None
_DB_PATH = "bot.db"

async def init_db() -> None:
    global _DB
    _DB = await aiosqlite.connect(_DB_PATH)
    await _DB.execute("PRAGMA foreign_keys=ON;")
    await _DB.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id INTEGER UNIQUE,
        first_name TEXT,
        username TEXT,
        is_admin INTEGER DEFAULT 0
    )""")
    await _DB.execute("""CREATE TABLE IF NOT EXISTS categories(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL
    )""")
    await _DB.execute("""CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT DEFAULT '',
        FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE CASCADE
    )""")
    await _DB.execute("""CREATE TABLE IF NOT EXISTS plans(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        price INTEGER NOT NULL,
        FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
    )""")
    await _DB.execute("""CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        plan_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'awaiting_proof',
        proof_type TEXT DEFAULT NULL,
        proof_value TEXT DEFAULT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        tracking_code TEXT UNIQUE,
        note TEXT DEFAULT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(product_id) REFERENCES products(id),
        FOREIGN KEY(plan_id) REFERENCES plans(id)
    )""")
    await _DB.execute("""CREATE TABLE IF NOT EXISTS settings(
        key TEXT PRIMARY KEY,
        value TEXT
    )""")
    
    # Safe ALTERs (idempotent)
    try:
        await _DB.execute("ALTER TABLE orders ADD COLUMN note TEXT DEFAULT NULL")
    except Exception:
        pass
    await _DB.commit()

async def get_db() -> aiosqlite.Connection:
    global _DB
    if _DB is None:
        await init_db()
    return _DB

async def fetchone(query: str, *params):
    db = await get_db()
    db.row_factory = aiosqlite.Row
    async with db.execute(query, params) as cursor:
        return await cursor.fetchone()

async def fetchall(query: str, *params) -> List[aiosqlite.Row]:
    db = await get_db()
    db.row_factory = aiosqlite.Row
    async with db.execute(query, params) as cursor:
        return await cursor.fetchall()

async def execute(query: str, *params) -> int:
    db = await get_db()
    cur = await db.execute(query, params)
    await db.commit()
    return cur.lastrowid

async def set_setting(key: str, value: str) -> None:
    await execute("""INSERT INTO settings(key, value) VALUES(?,?)
                     ON CONFLICT(key) DO UPDATE SET value=excluded.value""", key, value)

async def get_setting(key: str, default=None):
    row = await fetchone("SELECT value FROM settings WHERE key=?", key)
    return row["value"] if row and "value" in row.keys() and row["value"] is not None else default

async def upsert_user(tg_id: int, first_name: str, username: str, is_admin: int) -> None:
    await execute("""INSERT INTO users(tg_id, first_name, username, is_admin)
                     VALUES(?,?,?,?)
                     ON CONFLICT(tg_id) DO UPDATE SET first_name=excluded.first_name,
                       username=excluded.username, is_admin=excluded.is_admin""",
                  tg_id, first_name, username, is_admin)

async def get_or_create_user_id(tg_id: int) -> int:
    row = await fetchone("SELECT id FROM users WHERE tg_id=?", tg_id)
    if row:
        return int(row["id"])
    return await execute("INSERT INTO users(tg_id) VALUES(?)", tg_id)
