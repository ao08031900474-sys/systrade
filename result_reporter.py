
import pandas as pd
import numpy as np


def _calc_pf(df):
    if df is None or len(df) == 0:
        return 0.0

    win_sum = df[df["pnl"] > 0]["pnl"].sum()
    loss_sum = abs(df[df["pnl"] <= 0]["pnl"].sum())

    if loss_sum == 0:
        return np.inf if win_sum > 0 else 0.0

    return win_sum / loss_sum


def _calc_dd(df, initial_capital):
    if df is None or len(df) == 0:
        return 0.0

    d = df.sort_values("exit_date").copy()
    equity = initial_capital + d["pnl"].cumsum()
    peak = equity.cummax()
    dd = ((equity - peak) / peak).min()

    return float(dd)


def _basic_summary(df, config):
    if df is None or len(df) == 0:
        return {
            "trades": 0,
            "pf": 0.0,
            "wr": 0.0,
            "dd": 0.0,
            "ev": 0.0,
            "total_pnl": 0.0,
        }

    trades = len(df)
    pf = _calc_pf(df)
    wr = (df["pnl"] > 0).mean() * 100
    dd = _calc_dd(df, config.INITIAL_CAPITAL)
    ev = df["pnl"].mean()
    total_pnl = df["pnl"].sum()

    return {
        "trades": int(trades),
        "pf": float(pf),
        "wr": float(wr),
        "dd": float(dd),
        "ev": float(ev),
        "total_pnl": float(total_pnl),
    }


def _yearly_summary(df, config):
    if df is None or len(df) == 0:
        return pd.DataFrame()

    d = df.copy()
    d["signal_date"] = pd.to_datetime(d["signal_date"])
    d["year"] = d["signal_date"].dt.year

    rows = []

    for year, g in d.groupby("year"):
        s = _basic_summary(g, config)
        s["year"] = int(year)
        rows.append(s)

    return pd.DataFrame(rows)[
        ["year", "trades", "pf", "wr", "dd", "ev", "total_pnl"]
    ]


def _exit_reason_summary(df):
    if df is None or len(df) == 0:
        return pd.DataFrame()

    return (
        df.groupby("exit_reason")
        .agg(
            trades=("pnl", "count"),
            total_pnl=("pnl", "sum"),
            avg_pnl=("pnl", "mean"),
        )
        .reset_index()
    )


def generate_report(trade_df, label, config, save=True):
    """
    trade_dfを受け取り、標準フォーマットで成績を返す。
    同時にCSV/txtを保存する。
    """

    df = trade_df.copy() if trade_df is not None else pd.DataFrame()

    if len(df) > 0:
        df["signal_date"] = pd.to_datetime(df["signal_date"])
        df["entry_date"] = pd.to_datetime(df["entry_date"])
        df["exit_date"] = pd.to_datetime(df["exit_date"])

    full = _basic_summary(df, config)

    oos = df[
        (df["signal_date"] >= config.TEST_START) &
        (df["signal_date"] <= config.TEST_END)
    ].copy() if len(df) > 0 else pd.DataFrame()

    oos_summary = _basic_summary(oos, config)

    yearly = _yearly_summary(df, config)
    exit_summary = _exit_reason_summary(df)

    summary = {
        "label": label,

        "trades": full["trades"],
        "pf": full["pf"],
        "wr": full["wr"],
        "dd": full["dd"],
        "ev": full["ev"],
        "total_pnl": full["total_pnl"],

        "oos_trades": oos_summary["trades"],
        "oos_pf": oos_summary["pf"],
        "oos_wr": oos_summary["wr"],
        "oos_dd": oos_summary["dd"],
        "oos_ev": oos_summary["ev"],
        "oos_total_pnl": oos_summary["total_pnl"],
    }

    summary_df = pd.DataFrame([summary])

    if save:
        config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)

        trade_path = config.RESULTS_DIR / f"{label}_trades.csv"
        yearly_path = config.RESULTS_DIR / f"{label}_yearly.csv"
        exit_path = config.RESULTS_DIR / f"{label}_exit_reason.csv"
        summary_path = config.RESULTS_DIR / f"{label}_summary.csv"
        report_path = config.RESULTS_DIR / f"{label}_report.txt"

        df.to_csv(trade_path, index=False)
        yearly.to_csv(yearly_path, index=False)
        exit_summary.to_csv(exit_path, index=False)
        summary_df.to_csv(summary_path, index=False)

        text = []
        text.append("=" * 70)
        text.append(f"【REPORT: {label}】")
        text.append("=" * 70)
        text.append("")
        text.append("[FULL]")
        text.append(f"Trades: {summary['trades']}")
        text.append(f"PF    : {summary['pf']:.4f}")
        text.append(f"WR    : {summary['wr']:.2f}%")
        text.append(f"DD    : {summary['dd']:.2%}")
        text.append(f"EV    : {summary['ev']:.2f}")
        text.append(f"PNL   : {summary['total_pnl']:.2f}")
        text.append("")
        text.append("[OOS]")
        text.append(f"Trades: {summary['oos_trades']}")
        text.append(f"PF    : {summary['oos_pf']:.4f}")
        text.append(f"WR    : {summary['oos_wr']:.2f}%")
        text.append(f"DD    : {summary['oos_dd']:.2%}")
        text.append(f"EV    : {summary['oos_ev']:.2f}")
        text.append(f"PNL   : {summary['oos_total_pnl']:.2f}")

        report_path.write_text("\n".join(text), encoding="utf-8")

    return summary
