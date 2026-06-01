
import pandas as pd


def run_backtest(signal_df, price_df, config, label="backtest"):
    """
    元A0準拠バックテストエンジン。
    signal_df: ticker / signal_date / entry_date
    price_df : ticker / date / open / high / low / close
    """

    if signal_df is None or len(signal_df) == 0:
        return pd.DataFrame()

    sig = signal_df.copy()
    price = price_df.copy()

    sig["signal_date"] = pd.to_datetime(sig["signal_date"])
    sig["entry_date"] = pd.to_datetime(sig["entry_date"])

    price.columns = [c.lower() for c in price.columns]
    price["date"] = pd.to_datetime(price["date"])
    price = price.sort_values(["date", "ticker"]).reset_index(drop=True)

    all_dates = sorted(price["date"].unique())

    ohlc = {
        d: g.set_index("ticker")[["open", "high", "low", "close"]].to_dict("index")
        for d, g in price.groupby("date")
    }

    sig_by_date = {}
    for _, row in sig.iterrows():
        sig_by_date.setdefault(row["signal_date"], []).append({
            "ticker": row["ticker"],
            "signal_date": row["signal_date"],
            "entry_date": row["entry_date"],
        })

    cash = config.INITIAL_CAPITAL
    positions = {}
    pending = {}
    trades = []

    for d in all_dates:
        data = ohlc.get(d, {})

        # 1. pending注文を執行
        if d in pending:
            for order in pending[d]:
                ticker = order["ticker"]

                if ticker not in data:
                    continue
                if ticker in positions:
                    continue
                if len(positions) >= config.MAX_POSITIONS:
                    continue

                entry_price = data[ticker]["open"] * (1 + config.ENTRY_SLIPPAGE)
                stop_price = entry_price * (1 + config.STOP_LOSS)
                take_price = entry_price * (1 + config.TAKE_PROFIT)

                stop_distance = abs(entry_price * abs(config.STOP_LOSS))
                qty = int(cash * config.RISK_PER_TRADE / stop_distance) if stop_distance > 0 else 0

                if qty <= 0:
                    continue

                entry_cost = qty * entry_price * (1 + config.COMMISSION)

                if entry_cost > cash:
                    continue

                cash -= entry_cost

                positions[ticker] = {
                    "ticker": ticker,
                    "signal_date": order["signal_date"],
                    "entry_date": d,
                    "entry_price": entry_price,
                    "stop": stop_price,
                    "tp": take_price,
                    "qty": qty,
                    "days": 0,
                }

            del pending[d]

        # 2. 保有ポジション更新
        for ticker in list(positions.keys()):
            if ticker not in data:
                continue

            p = positions[ticker]
            p["days"] += 1

            exit_price = None
            exit_reason = None

            # 元A0準拠：SL優先
            if data[ticker]["low"] <= p["stop"]:
                exit_price = p["stop"] * (1 - config.EXIT_SLIPPAGE)
                exit_reason = "SL"
            elif data[ticker]["high"] >= p["tp"]:
                exit_price = p["tp"] * (1 - config.EXIT_SLIPPAGE)
                exit_reason = "TP"
            elif p["days"] >= config.MAX_HOLDING_DAYS:
                exit_price = data[ticker]["close"] * (1 - config.EXIT_SLIPPAGE)
                exit_reason = "TIME"

            if exit_price is not None:
                exit_value = p["qty"] * exit_price

                pnl = (
                    exit_value
                    - p["qty"] * p["entry_price"]
                    - (
                        p["qty"] * p["entry_price"] * config.COMMISSION
                        + exit_value * config.COMMISSION
                    )
                )

                cash += exit_value - exit_value * config.COMMISSION

                return_pct = (exit_price / p["entry_price"] - 1) * 100

                trades.append({
                    "label": label,
                    "ticker": ticker,
                    "signal_date": p["signal_date"],
                    "entry_date": p["entry_date"],
                    "entry_price": p["entry_price"],
                    "exit_date": d,
                    "exit_price": exit_price,
                    "exit_reason": exit_reason,
                    "qty": p["qty"],
                    "return_pct": return_pct,
                    "pnl": pnl,
                    "result": "win" if pnl > 0 else "loss",
                    "cash_after_exit": cash,
                })

                del positions[ticker]

        # 3. 当日signalを翌営業日pendingへ追加
        if d in sig_by_date:
            for s in sig_by_date[d]:
                pending.setdefault(s["entry_date"], []).append(s)

    return pd.DataFrame(trades)
