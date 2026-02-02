import sqlite3
import os
import json

APP_NAME = "RiskResearchApp"
DB_DIR = os.path.join(os.path.expanduser("~"), "AppData", "Local", APP_NAME)
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "trades.db")

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time TEXT,
        product TEXT,
        symbol TEXT,
        account REAL,
        risk_percent REAL,
        entry REAL,
        stop REAL,
        target REAL,
        position REAL,
        rr REAL,
        result REAL,
        reason TEXT,
        emotion TEXT
    )
    """)
    conn.commit()
    _auto_upgrade()

def _add_column(name, col_type):
    cursor.execute("PRAGMA table_info(trades)")
    cols = [c[1] for c in cursor.fetchall()]
    if name not in cols:
        cursor.execute(f"ALTER TABLE trades ADD COLUMN {name} {col_type}")
        conn.commit()

def _auto_upgrade():
    _add_column("institution_prices", "TEXT")
    _add_column("inst_avg", "REAL")
    _add_column("inst_median", "REAL")
    _add_column("inst_max", "REAL")
    _add_column("inst_min", "REAL")

def insert_trade(data: dict):
    cursor.execute("""
    INSERT INTO trades VALUES (
        NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
    )
    """, (
        data["time"], data["product"], data["symbol"],
        data["account"], data["risk_percent"],
        data["entry"], data["stop"], data["target"],
        data["position"], data["rr"], data["result"],
        data["reason"], data["emotion"],
        json.dumps(data["inst_prices"], ensure_ascii=False),
        data["inst_avg"], data["inst_median"],
        data["inst_max"], data["inst_min"]
    ))
    conn.commit()

def load_trades(product=None):
    if product:
        return cursor.execute(
            "SELECT * FROM trades WHERE product=? ORDER BY time DESC",
            (product,)
        ).fetchall()
    return cursor.execute("SELECT * FROM trades ORDER BY time DESC").fetchall()
