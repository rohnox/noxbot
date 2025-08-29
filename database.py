import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from config import DB_PATH, DEFAULT_LANG

def _connect():
    return sqlite3.connect(DB_PATH)

def now_iso():
    return datetime.utcnow().isoformat()

def init_db():
    con = _connect()
    cur = con.cursor()
    # users (ساده)
    cur.execute(
        """CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            username TEXT,
            lang TEXT,
            joined_at TEXT,
            banned INTEGER DEFAULT 0
        )"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS settings (
            user_id INTEGER,
            key TEXT,
            value TEXT,
            PRIMARY KEY (user_id, key)
        )"""
    )
    # products
    cur.execute(
        """CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE,
            title TEXT NOT NULL,
            description TEXT,
            price INTEGER NOT NULL,
            currency TEXT NOT NULL,
            active INTEGER DEFAULT 1,
            delivery_type TEXT NOT NULL, -- 'file' | 'license'
            file_id TEXT,
            stock_count INTEGER,
            created_at TEXT,
            updated_at TEXT
        )"""
    )
    # license pool
    cur.execute(
        """CREATE TABLE IF NOT EXISTS license_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            code TEXT UNIQUE NOT NULL,
            used INTEGER DEFAULT 0,
            used_order_id INTEGER,
            created_at TEXT,
            used_at TEXT
        )"""
    )
    # orders
    cur.execute(
        """CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            user_id INTEGER NOT NULL,
            status TEXT NOT NULL, -- new, invoice_sent, paid, processing, delivered, canceled, refunded, failed
            amount INTEGER NOT NULL,
            currency TEXT NOT NULL,
            created_at TEXT,
            updated_at TEXT,
            paid_at TEXT,
            delivered_at TEXT,
            admin_notified INTEGER DEFAULT 0
        )"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price INTEGER NOT NULL,
            total_price INTEGER NOT NULL
        )"""
    )
    # status history
    cur.execute(
        """CREATE TABLE IF NOT EXISTS order_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            note TEXT,
            created_at TEXT
        )"""
    )
    con.commit()
    con.close()

# ---------- users ----------
def upsert_user(user_id: int, first_name: str, last_name: Optional[str], username: Optional[str]) -> None:
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if cur.fetchone():
        cur.execute("UPDATE users SET first_name=?, last_name=?, username=? WHERE user_id=?",
                    (first_name, last_name, username, user_id))
    else:
        cur.execute("INSERT INTO users (user_id, first_name, last_name, username, lang, joined_at, banned)                    VALUES (?, ?, ?, ?, ?, ?, 0)",
                    (user_id, first_name, last_name, username, DEFAULT_LANG, now_iso()))
    con.commit()
    con.close()

def set_lang(user_id: int, lang: str) -> None:
    con = _connect()
    cur = con.cursor()
    cur.execute("UPDATE users SET lang=? WHERE user_id=?", (lang, user_id))
    con.commit()
    con.close()

def get_lang(user_id: int) -> str:
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT lang FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    con.close()
    return row[0] if row and row[0] else DEFAULT_LANG

def get_user_count() -> int:
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    n = cur.fetchone()[0]
    con.close()
    return n

def list_user_ids() -> List[int]:
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT user_id FROM users WHERE banned=0")
    rows = cur.fetchall()
    con.close()
    return [r[0] for r in rows]

def ban_user(user_id: int, banned: bool) -> None:
    con = _connect()
    cur = con.cursor()
    cur.execute("UPDATE users SET banned=? WHERE user_id=?", (1 if banned else 0, user_id))
    con.commit()
    con.close()

def is_banned(user_id: int) -> bool:
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT banned FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    con.close()
    return bool(row and row[0] == 1)

def set_setting(user_id: int, key: str, value: str) -> None:
    con = _connect()
    cur = con.cursor()
    cur.execute(
        """INSERT INTO settings (user_id, key, value) VALUES (?, ?, ?)
               ON CONFLICT(user_id, key) DO UPDATE SET value=excluded.value""", (user_id, key, value)
    )
    con.commit()
    con.close()

def get_setting(user_id: int, key: str, default=None):
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT value FROM settings WHERE user_id=? AND key=?", (user_id, key))
    row = cur.fetchone()
    con.close()
    return row[0] if row else default

# ---------- products ----------
def create_product(sku: str, title: str, description: str, price: int, currency: str, delivery_type: str, file_id: str=None, stock_count: int=None) -> int:
    con = _connect()
    cur = con.cursor()
    cur.execute("INSERT INTO products (sku, title, description, price, currency, active, delivery_type, file_id, stock_count, created_at, updated_at)                VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?)",
                (sku, title, description, price, currency, delivery_type, file_id, stock_count, now_iso(), now_iso()))
    con.commit()
    pid = cur.lastrowid
    con.close()
    return pid

def update_product(pid: int, **fields):
    if not fields:
        return
    con = _connect()
    cur = con.cursor()
    keys = ", ".join([f"{k}=?" for k in fields.keys()])
    values = list(fields.values())
    sql = f"UPDATE products SET {keys}, updated_at=? WHERE id=?"
    params = values + [now_iso(), pid]
    cur.execute(sql, params)
    con.commit()
    con.close()

def list_products(active_only=True) -> List[Tuple]:
    con = _connect()
    cur = con.cursor()
    if active_only:
        cur.execute("SELECT id, sku, title, description, price, currency, delivery_type, file_id, stock_count FROM products WHERE active=1 ORDER BY id DESC")
    else:
        cur.execute("SELECT id, sku, title, description, price, currency, delivery_type, file_id, stock_count, active FROM products ORDER BY id DESC")
    rows = cur.fetchall()
    con.close()
    return rows

def get_product(pid: int):
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT id, sku, title, description, price, currency, delivery_type, file_id, stock_count, active FROM products WHERE id=?", (pid,))
    row = cur.fetchone()
    con.close()
    return row

def add_license_codes(product_id: int, codes: List[str]) -> int:
    if not codes:
        return 0
    con = _connect()
    cur = con.cursor()
    inserted = 0
    for code in codes:
        try:
            cur.execute("INSERT INTO license_keys (product_id, code, created_at) VALUES (?, ?, ?)", (product_id, code.strip(), now_iso()))
            inserted += 1
        except Exception:
            pass
    con.commit()
    con.close()
    return inserted

def pop_license_code(product_id: int) -> Optional[str]:
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT id, code FROM license_keys WHERE product_id=? AND used=0 ORDER BY id ASC LIMIT 1", (product_id,))
    row = cur.fetchone()
    if not row:
        con.close()
        return None
    key_id, code = row
    cur.execute("UPDATE license_keys SET used=1, used_at=? WHERE id=?", (now_iso(), key_id))
    con.commit()
    con.close()
    return code

# ---------- orders ----------
def create_order(code: str, user_id: int, amount: int, currency: str) -> int:
    con = _connect()
    cur = con.cursor()
    cur.execute("INSERT INTO orders (code, user_id, status, amount, currency, created_at, updated_at)                VALUES (?, ?, 'new', ?, ?, ?, ?)",
                (code, user_id, amount, currency, now_iso(), now_iso()))
    con.commit()
    oid = cur.lastrowid
    con.close()
    return oid

def add_order_item(order_id: int, product_id: int, quantity: int, unit_price: int):
    con = _connect()
    cur = con.cursor()
    total = unit_price * quantity
    cur.execute("INSERT INTO order_items (order_id, product_id, quantity, unit_price, total_price) VALUES (?, ?, ?, ?, ?)",
                (order_id, product_id, quantity, unit_price, total))
    con.commit()
    con.close()

def set_order_status(order_id: int, status: str, note: str=None):
    con = _connect()
    cur = con.cursor()
    fields = ["status=?", "updated_at=?"]
    values = [status, now_iso()]
    if status == 'paid':
        fields.append("paid_at=?"); values.append(now_iso())
    if status == 'delivered':
        fields.append("delivered_at=?"); values.append(now_iso())
    cur.execute(f"UPDATE orders SET {', '.join(fields)} WHERE id=?", values + [order_id])
    cur.execute("INSERT INTO order_events (order_id, status, note, created_at) VALUES (?, ?, ?, ?)",
                (order_id, status, note, now_iso()))
    con.commit()
    con.close()

def mark_admin_notified(order_id: int):
    con = _connect()
    cur = con.cursor()
    cur.execute("UPDATE orders SET admin_notified=1 WHERE id=?", (order_id,))
    con.commit()
    con.close()

def get_order_by_code(code: str):
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT id, code, user_id, status, amount, currency, created_at, updated_at, paid_at, delivered_at, admin_notified FROM orders WHERE code=?", (code,))
    row = cur.fetchone()
    con.close()
    return row

def get_order(order_id: int):
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT id, code, user_id, status, amount, currency, created_at, updated_at, paid_at, delivered_at, admin_notified FROM orders WHERE id=?", (order_id,))
    row = cur.fetchone()
    con.close()
    return row

def list_orders(status: Optional[str]=None, limit: int=10, offset: int=0):
    con = _connect()
    cur = con.cursor()
    if status:
        cur.execute("SELECT id, code, user_id, status, amount, currency, created_at FROM orders WHERE status=? ORDER BY id DESC LIMIT ? OFFSET ?", (status, limit, offset))
    else:
        cur.execute("SELECT id, code, user_id, status, amount, currency, created_at FROM orders ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset))
    rows = cur.fetchall()
    con.close()
    return rows

def order_items(order_id: int) -> List[Tuple]:
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT product_id, quantity, unit_price, total_price FROM order_items WHERE order_id=?", (order_id,))
    rows = cur.fetchall()
    con.close()
    return rows

def revenue_sum() -> int:
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT COALESCE(SUM(amount),0) FROM orders WHERE status IN ('paid','delivered','processing','refunded')")
    total = cur.fetchone()[0]
    con.close()
    return total
