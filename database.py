import sqlite3
import datetime
from config import DATABASE_FILE

def init_db():
    conn = sqlite3.connect(DATABASE_FILE)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS subscriptions (user_id INTEGER PRIMARY KEY, expiry_date TEXT NOT NULL)")
    conn.commit()
    conn.close()

def get_subscription(user_id: int):
    conn = sqlite3.connect(DATABASE_FILE)
    cur = conn.cursor()
    cur.execute("SELECT expiry_date FROM subscriptions WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def set_subscription(user_id: int, days: int = 7):
    expiry = datetime.datetime.now() + datetime.timedelta(days=days)
    conn = sqlite3.connect(DATABASE_FILE)
    cur = conn.cursor()
    cur.execute("REPLACE INTO subscriptions (user_id, expiry_date) VALUES (?, ?)", (user_id, expiry.isoformat()))
    conn.commit()
    conn.close()

def is_subscription_valid(user_id: int) -> bool:
    expiry_str = get_subscription(user_id)
    if not expiry_str:
        return False
    return datetime.datetime.fromisoformat(expiry_str) > datetime.datetime.now()
