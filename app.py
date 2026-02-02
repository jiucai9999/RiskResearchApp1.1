import os
os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
import streamlit as st
import sqlite3
import os
from datetime import datetime
import pandas as pd
import json
import statistics

# ===============================
# 页面配置
# ===============================
st.set_page_config(page_title="多品种交易风控与研究系统", layout="wide")
st.title("📊 多品种交易 · 风控 & 研究系统")

# ===============================
# 数据库隔离
# ===============================
APP_NAME = "RiskResearchApp"
db_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", APP_NAME)
os.makedirs(db_dir, exist_ok=True)
DB_PATH = os.path.join(db_dir, "trades.db")

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

# ===============================
# 建表（基础结构）
# ===============================
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

# ===============================
# ⭐ 数据库自动升级（关键）
# ===============================
def add_column_if_not_exists(column, col_type):
    cursor.execute("PRAGMA table_info(trades)")
    existing = [c[1] for c in cursor.fetchall()]
    if column not in existing:
        cursor.execute(f"ALTER TABLE trades ADD COLUMN {column} {col_type}")
        conn.commit()

add_column_if_not_exists("institution_prices", "TEXT")
add_column_if_not_exists("inst_avg", "REAL")
add_column_if_not_exists("inst_median", "REAL")
add_column_if_not_exists("inst_max", "REAL")
add_column_if_not_exists("inst_min", "REAL")

# ===============================
# 工具函数
# ===============================
def load_trades(product=None):
    if product:
        return pd.read_sql(
            "SELECT * FROM trades WHERE product=? ORDER BY time ASC",
            conn,
            params=(product,)
        )
    return pd.read_sql("SELECT * FROM trades ORDER BY time ASC", conn)

# ===============================
# 品类 & 机构池
# ===============================
INSTITUTION_POOLS = {
    "黄金": ["高盛", "瑞银", "摩根士丹利", "花旗", "摩根大通", "美银"],
    "股票": ["高盛", "瑞银", "摩根士丹利", "中金", "中信", "华泰"],
    "基金": ["易方达", "南方基金", "富国", "广发", "博时"],
    "ETF": ["高盛", "瑞银", "摩根士丹利", "中金", "中信"]
}

# ===============================
# 品类选择（切换即清空机构勾选）
# ===============================
product = st.sidebar.selectbox("交易品类", list(INSTITUTION_POOLS.keys()))

if "last_product" not in st.session_state:
    st.session_state.last_product = product

if st.session_state.last_product != product:
    for k in list(st.session_state.keys()):
        if k.startswith("use_") or k.startswith("price_"):
            del st.session_state[k]
    st.session_state.last_product = product

# ===============================
# 下单前风控
# ===============================
st.subheader("🧮 下单前风控")

c1, c2 = st.columns(2)

with c1:
    account = st.number_input("账户资金", 100000.0, step=1000.0)
    risk_percent = st.number_input("单笔风险 %", 2.0, step=0.1)

with c2:
    entry_label = "入场价" if product == "黄金" else "买入价"
    entry = st.number_input(entry_label, 100.0)
    stop = st.number_input("止损价", 95.0)
    target = st.number_input("个人止盈价", 120.0)

symbol = st.text_input("📌 代码", "") if product != "黄金" else ""

# ===============================
# 机构预期价格（折叠）
# ===============================
inst_prices = {}
inst_values = []

selected_count = sum(
    1 for inst in INSTITUTION_POOLS[product]
    if st.session_state.get(f"use_{product}_{inst}")
)

with st.expander(f"🏦 投资机构预期价格（已选 {selected_count} 家）", expanded=False):
    for inst in INSTITUTION_POOLS[product]:
        col1, col2 = st.columns([1, 2])
        use_key = f"use_{product}_{inst}"
        price_key = f"price_{product}_{inst}"

        with col1:
            use = st.checkbox(inst, key=use_key)

        with col2:
            price = st.number_input(
                f"{inst} 预期价",
                value=0.0,
                key=price_key,
                disabled=not use
            )

        if use and price > 0:
            inst_prices[inst] = price
            inst_values.append(price)

# ===============================
# 机构统计
# ===============================
if inst_values:
    inst_avg = sum(inst_values) / len(inst_values)
    inst_median = statistics.median(inst_values)
    inst_max = max(inst_values)
    inst_min = min(inst_values)

    st.info(
        f"📊 机构统计 ｜ 均值 {inst_avg:.2f} ｜ 中位 {inst_median:.2f} ｜ "
        f"最大 {inst_max:.2f} ｜ 最小 {inst_min:.2f}"
    )
else:
    inst_avg = inst_median = inst_max = inst_min = None

# ===============================
# 情绪 & 理由
# ===============================
reason = st.text_area("🧠 交易理由（可选）")
emotion = st.selectbox("😐 交易情绪", ["冷静", "犹豫", "冲动", "恐惧", "自信"])

# ===============================
# 风控计算
# ===============================
position = rr = 0.0

if st.button("✅ 计算风控"):
    loss = abs(entry - stop)
    if loss == 0:
        st.error("止损不能等于入场价")
        st.stop()

    risk_amt = account * risk_percent / 100
    position = risk_amt / loss
    rr = abs(target - entry) / loss
    st.success(f"📦 仓位 {position:.2f} ｜ 📊 盈亏比 {rr:.2f}")

# ===============================
# 保存交易
# ===============================
st.divider()
st.subheader("✍️ 交易结果")

result = st.number_input("本笔结果（盈正 / 亏负）", 0.0, step=100.0)

if st.button("💾 保存交易"):
    cursor.execute(
        """
        INSERT INTO trades (
            time, product, symbol, account, risk_percent,
            entry, stop, target,
            position, rr, result,
            reason, emotion,
            institution_prices,
            inst_avg, inst_median, inst_max, inst_min
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            product, symbol, account, risk_percent,
            entry, stop, target,
            position, rr, result,
            reason, emotion,
            json.dumps(inst_prices, ensure_ascii=False),
            inst_avg, inst_median, inst_max, inst_min
        )
    )
    conn.commit()
    st.success("✅ 交易已保存")
    st.rerun()

# ===============================
# 最近 10 笔交易
# ===============================
st.divider()
st.subheader("📋 最近 10 笔交易（当前品类）")

df_recent = pd.read_sql(
    """
    SELECT
        time AS 时间,
        symbol AS 代码,
        entry AS 入场价,
        stop AS 止损价,
        target AS 止盈价,
        result AS 本笔盈亏
    FROM trades
    WHERE product=?
    ORDER BY time DESC
    LIMIT 10
    """,
    conn,
    params=(product,)
)

if df_recent.empty:
    st.info("当前品类暂无交易")
else:
    st.dataframe(df_recent, use_container_width=True)

# ===============================
# CSV 导出
# ===============================
st.divider()
st.subheader("⬇️ 导出交易数据")

scope = st.radio("导出范围", ["当前品类", "全部品类"], horizontal=True)

df_export = load_trades(product) if scope == "当前品类" else load_trades()
filename = f"trades_{product}.csv" if scope == "当前品类" else "trades_all.csv"

if df_export.empty:
    st.warning("当前没有可导出的数据")
else:
    st.download_button(
        "📥 下载 CSV",
        data=df_export.to_csv(index=False, encoding="utf-8-sig"),
        file_name=filename,
        mime="text/csv"
    )