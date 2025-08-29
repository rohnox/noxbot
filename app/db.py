# -*- coding: utf-8 -*-
import aiosqlite
from app.config import settings

_DB: aiosqlite.Connection | None = None

async def init_db():
    global _DB
    if _DB is None:
        _DB = await aiosqlite.connect(settings.db_path)
        _DB.row_factory = aiosqlite.Row
        await _DB.execute("PRAGMA foreign_keys = ON;")
        await _DB.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER UNIQUE,
            first_name TEXT,
            username TEXT,
            is_blocked INTEGER DEFAULT 0
        );
        """)
        await _DB.execute("""
        CREATE TABLE IF NOT EXISTS products(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL
        );
        """)
        await _DB.execute("""
        CREATE TABLE IF NOT EXISTS plans(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            price INTEGER NOT NULL,
            FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
        );
        """)
        await _DB.execute("""
        CREATE TABLE IF NOT EXISTS orders(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            plan_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            tracking_code TEXT,
            created_at TEXT,
            proof_type TEXT,
            proof_value TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(product_id) REFERENCES products(id),
            FOREIGN KEY(plan_id) REFERENCES plans(id)
        );
        """)
        await _DB.execute("""
        CREATE TABLE IF NOT EXISTS settings(
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """)
        await _DB.commit()
        # مهاجرت نرم برای ستون‌های احتمالی قدیمی
        await _ensure_columns()

async def _ensure_columns():
    # ستون‌هایی که ممکن است در نسخه‌های قدیمی نباشند
    need_cols = {
        "orders": ["tracking_code", "created_at", "proof_type", "proof_value"],
    }
    for table, cols in need_cols.items():
        info = await fetchall(f"PRAGMA table_info({table})")
        names = { (r["name"] if isinstance(r, dict) else r[1]) for r in info } if info else set()
        for col in cols:
            if col not in names:
                try:
                    if col == "created_at":
                        await execute(f"ALTER TABLE {table} ADD COLUMN {col} TEXT")
                    elif col in ("proof_type", "proof_value", "tracking_code"):
                        await execute(f"ALTER TABLE {table} ADD COLUMN {col} TEXT")
                except Exception:
                    pass  # اگر قبلاً اضافه شده یا خطای جزئی، عبور

async def execute(query: str, *params):
    db = _DB
    if db is None:
        await init_db()
        db = _DB
    cur = await db.execute(query, params)
    await db.commit()
    # اگر INSERT بود، lastrowid برگردان
    try:
        return cur.lastrowid
    except Exception:
        return None

async def fetchone(query: str, *params):
    db = _DB
    if db is None:
        await init_db()
        db = _DB
    cur = await db.execute(query, params)
    row = await cur.fetchone()
    return row

async def fetchall(query: str, *params):
    db = _DB
    if db is None:
        await init_db()
        db = _DB
    cur = await db.execute(query, params)
    rows = await cur.fetchall()
    return rows

async def get_setting(key: str, default=None):
    row = await fetchone("SELECT value FROM settings WHERE key=?", key)
    if not row:
        return default
    try:
        return row["value"]
    except Exception:
        return default

async def upsert_user(tg_id: int, first_name: str, username: str, is_blocked: int = 0):
    await execute(
        """INSERT INTO users(tg_id, first_name, username, is_blocked)
           VALUES(?,?,?,?)
           ON CONFLICT(tg_id) DO UPDATE SET
             first_name=excluded.first_name,
             username=excluded.username,
             is_blocked=excluded.is_blocked
        """,
        tg_id, first_name, username, is_blocked
    )
