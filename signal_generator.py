
import pandas as pd
import numpy as np


def prepare_nikkei(nikkei_df):
    nikkei = nikkei_df.copy()
    nikkei.columns = [c.lower() for c in nikkei.columns]

    if "date" not in nikkei.columns:
        nikkei = nikkei.reset_index()
        nikkei.columns = [c.lower() for c in nikkei.columns]

    nikkei["date"] = pd.to_datetime(nikkei["date"])
    nikkei = nikkei.sort_values("date").reset_index(drop=True)
    nikkei["ma200"] = nikkei["close"].rolling(200).mean()
    nikkei = nikkei.set_index("date")

    return nikkei


def get_market_status(date_check, nikkei, config):
    date_check = pd.Timestamp(date_check)

    try:
        idx = nikkei.index.searchsorted(date_check)

        if idx == len(nikkei):
            idx = len(nikkei) - 1
        elif nikkei.index[idx] != date_check and idx > 0:
            idx = idx - 1

        row = nikkei.iloc[idx]

        if pd.isna(row["ma200"]):
            return "unknown"

        return "bullish" if row["close"] > row["ma200"] * config.NIKKEI_MA_RATIO else "bearish"

    except Exception:
        return "unknown"


def generate_signals(
    price_df,
    nikkei_df,
    config,
    gap_threshold=None,
    vol_threshold=None,
    use_gap=True,
    use_vol=True,
    use_prev=True,
    use_curr=True,
    use_ma=True,
    use_market=True,
    label="signal"
):
    """
    元A0準拠のsignal generator。

    Pattern例：
    A: use_gap=True,  use_vol=False, use_prev=False, use_curr=False, use_ma=False, use_market=False
    B: use_gap=True,  use_vol=True,  use_prev=False, use_curr=False, use_ma=False, use_market=False
    C: use_gap=True,  use_vol=True,  use_prev=True,  use_curr=True,  use_ma=True,  use_market=False
    D: use_gap=True,  use_vol=True,  use_prev=True,  use_curr=True,  use_ma=True,  use_market=True
    """

    gap_threshold = config.GAP_THRESHOLD if gap_threshold is None else gap_threshold
    vol_threshold = config.VOL_THRESHOLD if vol_threshold is None else vol_threshold

    price = price_df.copy()
    price.columns = [c.lower() for c in price.columns]
    price["date"] = pd.to_datetime(price["date"])
    price = price.sort_values(["ticker", "date"]).reset_index(drop=True)

    nikkei = prepare_nikkei(nikkei_df)

    signals = []
    details = []

    for ticker in price["ticker"].unique():
        df = price[price["ticker"] == ticker].copy().sort_values("date").reset_index(drop=True)

        if len(df) < 25:
            continue

        df["prev_open"] = df["open"].shift(1)
        df["two_days_ago_close"] = df["close"].shift(2)
        df["prev_close"] = df["close"].shift(1)
        df["prev_high"] = df["high"].shift(1)
        df["prev_low"] = df["low"].shift(1)
        df["prev_volume"] = df["volume"].shift(1)

        # 元A0完全準拠
        df["gap"] = ((df["prev_open"] / df["two_days_ago_close"] - 1) * 100)
        df["vol_ma"] = df["volume"].rolling(window=20).mean()
        df["vol_ratio"] = df["prev_volume"] / df["vol_ma"]

        df["prev_ma20"] = df["close"].shift(1).rolling(window=20).mean()
        df["curr_ma20"] = df["close"].rolling(window=20).mean()
        df["range"] = df["prev_high"] - df["prev_low"]

        df["f_gap"] = df["gap"] >= gap_threshold
        df["f_vol"] = df["vol_ratio"] >= vol_threshold

        df["f_prev"] = (
            (df["prev_open"] > df["two_days_ago_close"] * 1.02) &
            (df["prev_close"] > df["prev_low"] + df["range"] * 0.6)
        )

        df["f_curr"] = df["close"] > df["prev_close"]

        df["f_ma"] = (
            (df["close"] > df["curr_ma20"]) &
            (df["prev_close"] > df["prev_ma20"])
        )

        cond = pd.Series(True, index=df.index)

        if use_gap:
            cond &= df["f_gap"]
        if use_vol:
            cond &= df["f_vol"]
        if use_prev:
            cond &= df["f_prev"]
        if use_curr:
            cond &= df["f_curr"]
        if use_ma:
            cond &= df["f_ma"]

        for idx, row in df[cond].iterrows():
            if idx + 1 >= len(df):
                continue

            signal_date = row["date"]
            entry_date = df.loc[idx + 1, "date"]
            market = get_market_status(signal_date, nikkei, config)

            if use_market and market != "bullish":
                continue

            base = {
                "label": label,
                "ticker": ticker,
                "signal_date": signal_date,
                "entry_date": entry_date,
            }

            detail = {
                **base,
                "signal_close": row["close"],
                "market": market,
                "gap": row["gap"],
                "vol_ratio": row["vol_ratio"],
                "f_gap": bool(row["f_gap"]),
                "f_vol": bool(row["f_vol"]),
                "f_prev": bool(row["f_prev"]),
                "f_curr": bool(row["f_curr"]),
                "f_ma": bool(row["f_ma"]),
                "gap_threshold": gap_threshold,
                "vol_threshold": vol_threshold,
                "use_gap": use_gap,
                "use_vol": use_vol,
                "use_prev": use_prev,
                "use_curr": use_curr,
                "use_ma": use_ma,
                "use_market": use_market,
            }

            signals.append(base)
            details.append(detail)

    signal_df = pd.DataFrame(signals)
    detail_df = pd.DataFrame(details)

    return signal_df, detail_df


def pattern_params(pattern_name):
    """
    標準Pattern定義。
    """
    patterns = {
        "A_gap_only": {
            "use_gap": True,
            "use_vol": False,
            "use_prev": False,
            "use_curr": False,
            "use_ma": False,
            "use_market": False,
        },
        "B_gap_vol": {
            "use_gap": True,
            "use_vol": True,
            "use_prev": False,
            "use_curr": False,
            "use_ma": False,
            "use_market": False,
        },
        "C_gap_vol_6cond": {
            "use_gap": True,
            "use_vol": True,
            "use_prev": True,
            "use_curr": True,
            "use_ma": True,
            "use_market": False,
        },
        "D_full_A0": {
            "use_gap": True,
            "use_vol": True,
            "use_prev": True,
            "use_curr": True,
            "use_ma": True,
            "use_market": True,
        },
    }

    if pattern_name not in patterns:
        raise ValueError(f"Unknown pattern: {pattern_name}")

    return patterns[pattern_name]
