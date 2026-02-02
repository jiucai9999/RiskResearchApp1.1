import streamlit as st
import statistics
import pandas as pd
from controller.trade_controller import calc_risk, build_trade_dict
from model.database import insert_trade, load_trades

INSTITUTIONS = {
    "黄金": ["高盛", "瑞银", "摩根士丹利", "花旗"],
    "股票": ["高盛", "中金", "中信"],
    "基金": ["易方达", "南方基金"],
    "ETF": ["高盛", "摩根士丹利"]
}

def render():
    st.title("📊 多品种交易 · 风控 & 研究系统")

    product = st.sidebar.selectbox("交易品类", list(INSTITUTIONS.keys()))

    c1, c2 = st.columns(2)
    with c1:
        account = st.number_input("账户资金", 100000.0)
        risk_percent = st.number_input("单笔风险 %", 2.0)
    with c2:
        entry = st.number_input("入场价", 100.0)
        stop = st.number_input("止损价", 95.0)
        target = st.number_input("止盈价", 120.0)

    symbol = st.text_input("代码", "")

    inst_prices = {}
    inst_values = []

    with st.expander("🏦 机构预测"):
        for inst in INSTITUTIONS[product]:
            use = st.checkbox(inst, key=f"use_{inst}")
            price = st.number_input(inst, key=f"price_{inst}", disabled=not use)
            if use and price > 0:
                inst_prices[inst] = price
                inst_values.append(price)

    if inst_values:
        st.info(
            f"均值 {statistics.mean(inst_values):.2f} ｜ "
            f"中位 {statistics.median(inst_values):.2f}"
        )

    reason = st.text_area("交易理由")
    emotion = st.selectbox("情绪", ["冷静", "犹豫", "冲动", "恐惧", "自信"])

    if st.button("计算风控"):
        pos, rr = calc_risk(account, risk_percent, entry, stop, target)
        st.success(f"仓位 {pos:.2f} ｜ RR {rr:.2f}")

    result = st.number_input("结果", 0.0)

    if st.button("保存交易"):
        insert_trade(build_trade_dict(
            product=product,
            symbol=symbol,
            account=account,
            risk_percent=risk_percent,
            entry=entry,
            stop=stop,
            target=target,
            position=pos,
            rr=rr,
            result=result,
            reason=reason,
            emotion=emotion,
            inst_prices=inst_prices,
            inst_avg=statistics.mean(inst_values) if inst_values else None,
            inst_median=statistics.median(inst_values) if inst_values else None,
            inst_max=max(inst_values) if inst_values else None,
            inst_min=min(inst_values) if inst_values else None
        ))
        st.success("已保存")

    st.divider()
    rows = load_trades(product)
    if rows:
        df = pd.DataFrame(rows, columns=[
            "id","时间","品类","代码","账户","风险%",
            "入场","止损","止盈","仓位","RR","结果",
            "理由","情绪","机构","均","中","高","低"
        ])
        st.dataframe(df)
