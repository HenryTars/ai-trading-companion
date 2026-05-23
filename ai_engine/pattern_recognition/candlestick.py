import pandas as pd


def detect_candlestick_patterns(df: pd.DataFrame) -> list[dict]:
    if len(df) < 3:
        return []

    results = []

    for i in range(2, len(df)):
        o  = float(df["Open"].iloc[i])
        h  = float(df["High"].iloc[i])
        l  = float(df["Low"].iloc[i])
        c  = float(df["Close"].iloc[i])
        o1 = float(df["Open"].iloc[i - 1])
        c1 = float(df["Close"].iloc[i - 1])

        body  = abs(c - o)
        rng   = h - l
        if rng == 0:
            continue
        lower_wick = min(o, c) - l
        upper_wick = h - max(o, c)

        def _p(ptype, bias, conf):
            results.append({
                "type":      ptype,
                "index":     i,
                "timestamp": str(df.index[i]),
                "bias":      bias,
                "confidence": conf,
            })

        # Doji
        if body / rng < 0.10:
            _p("Doji", "neutral", 0.55)

        # Hammer
        if lower_wick > 2 * body and upper_wick < body and body / rng < 0.40:
            _p("Hammer", "bullish", 0.68)

        # Shooting Star
        if upper_wick > 2 * body and lower_wick < body and body / rng < 0.40:
            _p("Shooting Star", "bearish", 0.68)

        # Bullish Engulfing
        if c1 < o1 and c > o and c > o1 and o < c1:
            _p("Bullish Engulfing", "bullish", 0.72)

        # Bearish Engulfing
        if c1 > o1 and c < o and c < o1 and o > c1:
            _p("Bearish Engulfing", "bearish", 0.72)

        # Marubozu (body ≥ 90 % of range)
        if body / rng >= 0.90:
            label = "Bullish Marubozu" if c > o else "Bearish Marubozu"
            _p(label, "bullish" if c > o else "bearish", 0.65)

    return results[-10:]
