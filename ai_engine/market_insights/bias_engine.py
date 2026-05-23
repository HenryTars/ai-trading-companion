import pandas as pd
from ai_engine.chart_analysis.analyzer import analyze_chart


def generate_bias(df: pd.DataFrame, symbol: str = "", timeframe: str = "H1") -> dict:
    """Full AI bias report with scenarios and invalidation levels."""
    analysis = analyze_chart(df, symbol, timeframe)
    if "error" in analysis:
        return analysis

    bias  = analysis["bias"]
    sr    = analysis["support_resistance"]
    ns    = f"{sr['nearest_support']:.5f}"    if sr.get("nearest_support")    else "—"
    nr    = f"{sr['nearest_resistance']:.5f}" if sr.get("nearest_resistance") else "—"
    conf  = analysis["confidence"]

    certainty = "strong" if conf >= 0.75 else ("moderate" if conf >= 0.55 else "weak")

    if bias == "bullish":
        scenarios = [
            f"**Primary — Bullish continuation:** Price pushes toward resistance at {nr}.",
            f"**Alternate — Pullback:** Price retraces to support at {ns} before resuming higher.",
            f"**Invalidation:** Decisive close below {ns} on elevated volume.",
        ]
    elif bias == "bearish":
        scenarios = [
            f"**Primary — Bearish continuation:** Price moves toward support at {ns}.",
            f"**Alternate — Bounce:** Price tests resistance at {nr} before resuming lower.",
            f"**Invalidation:** Decisive close above {nr} on elevated volume.",
        ]
    else:
        scenarios = [
            f"**Primary — Range continuation:** Price oscillates between {ns} and {nr}.",
            f"**Alternate — Breakout:** A strong directional close beyond either level signals a new trend.",
            f"**Invalidation:** Strong close with momentum outside the established range.",
        ]

    analysis["scenarios"] = scenarios
    analysis["certainty"] = certainty
    return analysis
