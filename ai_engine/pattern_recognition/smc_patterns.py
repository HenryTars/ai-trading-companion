import pandas as pd


def _fvg(df: pd.DataFrame) -> list[dict]:
    out = []
    for i in range(2, len(df)):
        h_prev = float(df["High"].iloc[i - 2])
        l_prev = float(df["Low"].iloc[i - 2])
        h_curr = float(df["High"].iloc[i])
        l_curr = float(df["Low"].iloc[i])

        if h_prev < l_curr:          # bullish gap
            out.append({"type": "Bullish FVG",  "index": i,
                        "timestamp": str(df.index[i]),
                        "top": l_curr, "bottom": h_prev,
                        "bias": "bullish", "confidence": 0.70})
        if l_prev > h_curr:          # bearish gap
            out.append({"type": "Bearish FVG",  "index": i,
                        "timestamp": str(df.index[i]),
                        "top": l_prev, "bottom": h_curr,
                        "bias": "bearish", "confidence": 0.70})
    return out[-5:]


def _order_blocks(df: pd.DataFrame) -> list[dict]:
    out = []
    for i in range(1, len(df) - 1):
        o, c  = float(df["Open"].iloc[i]),     float(df["Close"].iloc[i])
        o2, c2 = float(df["Open"].iloc[i + 1]), float(df["Close"].iloc[i + 1])
        move  = c2 - o2

        # Bullish OB: bearish candle followed by stronger bullish candle
        if c < o and move > 0 and move > abs(c - o):
            out.append({"type": "Bullish Order Block", "index": i,
                        "timestamp": str(df.index[i]),
                        "high": float(df["High"].iloc[i]),
                        "low":  float(df["Low"].iloc[i]),
                        "bias": "bullish", "confidence": 0.73})
        # Bearish OB: bullish candle followed by stronger bearish candle
        if c > o and move < 0 and abs(move) > abs(c - o):
            out.append({"type": "Bearish Order Block", "index": i,
                        "timestamp": str(df.index[i]),
                        "high": float(df["High"].iloc[i]),
                        "low":  float(df["Low"].iloc[i]),
                        "bias": "bearish", "confidence": 0.73})
    return out[-5:]


def _bos(df: pd.DataFrame, window: int = 10) -> list[dict]:
    out = []
    last_idx = -999

    for i in range(window, len(df)):
        recent_high = float(df["High"].iloc[i - window: i].max())
        recent_low  = float(df["Low"].iloc[i - window: i].min())
        close       = float(df["Close"].iloc[i])

        if i - last_idx < 5:       # de-duplicate nearby signals
            continue
        if close > recent_high:
            out.append({"type": "BOS (Bullish)", "index": i,
                        "timestamp": str(df.index[i]),
                        "level": recent_high, "bias": "bullish", "confidence": 0.67})
            last_idx = i
        elif close < recent_low:
            out.append({"type": "BOS (Bearish)", "index": i,
                        "timestamp": str(df.index[i]),
                        "level": recent_low,  "bias": "bearish", "confidence": 0.67})
            last_idx = i
    return out[-3:]


def detect_smc_patterns(df: pd.DataFrame) -> list[dict]:
    if len(df) < 10:
        return []
    all_p = _fvg(df) + _order_blocks(df) + _bos(df)
    return sorted(all_p, key=lambda x: x["index"])[-10:]
