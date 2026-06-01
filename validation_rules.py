
def validate(summary, config):
    """
    summary_dictを受け取り、
    ADOPT / REJECT / HOLD を返す。
    """

    reasons = []

    trades = summary.get("trades", 0)
    pf = summary.get("pf", 0)
    dd = summary.get("dd", 0)

    oos_trades = summary.get("oos_trades", 0)
    oos_pf = summary.get("oos_pf", 0)
    oos_dd = summary.get("oos_dd", 0)

    # ========================================================
    # 即時却下
    # ========================================================

    if trades < config.REJECT_TRADES_LT:
        reasons.append(f"全期間Trade数不足: {trades} < {config.REJECT_TRADES_LT}")

    if pf < config.REJECT_PF_LT:
        reasons.append(f"全期間PF不足: {pf:.3f} < {config.REJECT_PF_LT}")

    if dd < config.REJECT_DD_LT:
        reasons.append(f"全期間DD悪化: {dd:.2%} < {config.REJECT_DD_LT:.2%}")

    if oos_trades < config.REJECT_OOS_TRADES_LT:
        reasons.append(f"OOS Trade数不足: {oos_trades} < {config.REJECT_OOS_TRADES_LT}")

    if oos_dd < config.REJECT_OOS_DD_LT:
        reasons.append(f"OOS DD悪化: {oos_dd:.2%} < {config.REJECT_OOS_DD_LT:.2%}")

    if reasons:
        return {
            "decision": "REJECT",
            "reasons": reasons,
            "report": "\n".join(reasons),
        }

    # ========================================================
    # 採用
    # ========================================================

    adopt_ok = (
        trades >= config.MIN_TRADES_ADOPT and
        pf >= config.MIN_PF_ADOPT and
        dd >= config.MAX_DD_ADOPT and
        oos_pf >= config.MIN_OOS_PF_ADOPT
    )

    if adopt_ok:
        return {
            "decision": "ADOPT",
            "reasons": ["採用条件を満たす"],
            "report": "採用条件を満たす",
        }

    # ========================================================
    # 保留
    # ========================================================

    hold_reasons = []

    if trades < config.MIN_TRADES_ADOPT:
        hold_reasons.append(f"採用にはTrade数不足: {trades} < {config.MIN_TRADES_ADOPT}")

    if pf < config.MIN_PF_ADOPT:
        hold_reasons.append(f"採用にはPF不足: {pf:.3f} < {config.MIN_PF_ADOPT}")

    if dd < config.MAX_DD_ADOPT:
        hold_reasons.append(f"採用にはDDが深い: {dd:.2%} < {config.MAX_DD_ADOPT:.2%}")

    if oos_pf < config.MIN_OOS_PF_ADOPT:
        hold_reasons.append(f"採用にはOOS PF不足: {oos_pf:.3f} < {config.MIN_OOS_PF_ADOPT}")

    return {
        "decision": "HOLD",
        "reasons": hold_reasons,
        "report": "\n".join(hold_reasons),
    }
