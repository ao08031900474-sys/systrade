
import pandas as pd
from datetime import datetime


def run_research(signal_df, price_df, label, mods):
    """
    研究基盤の標準実行関数。

    signal_df + price_df + label を渡すだけで、
    backtest → report → validation → decision log
    まで実行する。
    """

    config = mods["config"]
    backtest_engine = mods["backtest_engine"]
    result_reporter = mods["result_reporter"]
    validation_rules = mods["validation_rules"]

    print("=" * 70)
    print(f"【RUN RESEARCH】{label}")
    print("=" * 70)

    trade_df = backtest_engine.run_backtest(
        signal_df=signal_df,
        price_df=price_df,
        config=config,
        label=label
    )

    summary = result_reporter.generate_report(
        trade_df=trade_df,
        label=label,
        config=config,
        save=True
    )

    validation = validation_rules.validate(
        summary=summary,
        config=config
    )

    row = {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "label": label,
        "decision": validation["decision"],
        "reasons": " / ".join(validation["reasons"]),

        "trades": summary.get("trades"),
        "pf": summary.get("pf"),
        "wr": summary.get("wr"),
        "dd": summary.get("dd"),
        "ev": summary.get("ev"),
        "total_pnl": summary.get("total_pnl"),

        "oos_trades": summary.get("oos_trades"),
        "oos_pf": summary.get("oos_pf"),
        "oos_wr": summary.get("oos_wr"),
        "oos_dd": summary.get("oos_dd"),
        "oos_ev": summary.get("oos_ev"),
        "oos_total_pnl": summary.get("oos_total_pnl"),
    }

    log_path = config.DECISION_LOG

    if log_path.exists():
        old = pd.read_csv(log_path)
        new = pd.concat([old, pd.DataFrame([row])], ignore_index=True)
    else:
        new = pd.DataFrame([row])

    new.to_csv(log_path, index=False)

    print("")
    print("【SUMMARY】")
    print(pd.DataFrame([summary]))

    print("")
    print("【VALIDATION】")
    print(validation["decision"])
    print(validation["report"])

    print("")
    print("保存:", log_path)

    return {
        "trade_df": trade_df,
        "summary": summary,
        "validation": validation,
    }
