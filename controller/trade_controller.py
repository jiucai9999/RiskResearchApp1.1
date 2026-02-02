from datetime import datetime

def calc_risk(account, risk_percent, entry, stop, target):
    loss = abs(entry - stop)
    if loss == 0:
        raise ValueError("止损不能等于入场价")

    risk_amt = account * risk_percent / 100
    position = risk_amt / loss
    rr = abs(target - entry) / loss
    return position, rr

def build_trade_dict(**kwargs):
    kwargs["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return kwargs
