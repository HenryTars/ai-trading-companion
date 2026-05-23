import pandas as pd
import numpy as np


def swing_highs(df: pd.DataFrame, lookback: int = 5) -> list[int]:
    h = df["High"]
    result = []
    for i in range(lookback, len(df) - lookback):
        window = h.iloc[i - lookback: i + lookback + 1]
        if float(h.iloc[i]) == float(window.max()):
            result.append(i)
    return result


def swing_lows(df: pd.DataFrame, lookback: int = 5) -> list[int]:
    l = df["Low"]
    result = []
    for i in range(lookback, len(df) - lookback):
        window = l.iloc[i - lookback: i + lookback + 1]
        if float(l.iloc[i]) == float(window.min()):
            result.append(i)
    return result


def get_trend(df: pd.DataFrame) -> dict:
    """Determine trend via EMA alignment (20/50/200)."""
    c = df["Close"]
    e20  = float(c.ewm(span=20,  adjust=False).mean().iloc[-1])
    e50  = float(c.ewm(span=50,  adjust=False).mean().iloc[-1]) if len(df) >= 50  else None
    e200 = float(c.ewm(span=200, adjust=False).mean().iloc[-1]) if len(df) >= 200 else None
    last = float(c.iloc[-1])

    score = 0
    score +=  1 if last > e20  else -1
    if e50:   score += 1 if last > e50  else -1
    if e200:  score += 1 if last > e200 else -1

    direction = "bullish" if score >= 2 else ("bearish" if score <= -2 else "ranging")
    strength  = "strong"  if abs(score) == 3 else ("moderate" if abs(score) == 2 else "weak")

    return {
        "direction": direction,
        "strength":  strength,
        "score":     score,
        "ema20":     round(e20, 5),
        "ema50":     round(e50, 5) if e50 else None,
        "ema200":    round(e200, 5) if e200 else None,
    }


def get_support_resistance(df: pd.DataFrame,
                           lookback: int = 5,
                           max_levels: int = 4) -> dict:
    sh_idx = swing_highs(df, lookback)
    sl_idx = swing_lows(df,  lookback)
    price  = float(df["Close"].iloc[-1])

    resistance = sorted(
        [float(df["High"].iloc[i]) for i in sh_idx if float(df["High"].iloc[i]) > price]
    )[:max_levels]

    support = sorted(
        [float(df["Low"].iloc[i]) for i in sl_idx if float(df["Low"].iloc[i]) < price],
        reverse=True,
    )[:max_levels]

    return {
        "support":            support,
        "resistance":         resistance,
        "nearest_support":    support[0]    if support    else None,
        "nearest_resistance": resistance[0] if resistance else None,
    }
