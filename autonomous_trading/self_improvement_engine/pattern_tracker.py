"""
Pattern Tracker
Reads closed paper trades and builds a performance map:
  - Win rate per strategy / session / direction / confidence band
  - Tracks improvement over time
  - Identifies what conditions produce the best results
"""
import json
from pathlib import Path
from typing import Dict, List
from collections import defaultdict

TRACKER_FILE = Path(__file__).resolve().parent.parent.parent / "database" / "pattern_stats.json"


def _load_paper_trades() -> List[Dict]:
    state_file = Path(__file__).resolve().parent.parent.parent / "database" / "paper_account.json"
    if not state_file.exists():
        return []
    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
        return data.get("closed_trades", [])
    except Exception:
        return []


def _band(conf: float) -> str:
    if conf >= 0.80: return "High (80%+)"
    if conf >= 0.65: return "Medium (65–80%)"
    return "Low (<65%)"


def build_stats(trades: List[Dict] = None) -> Dict:
    if trades is None:
        trades = _load_paper_trades()

    closed = [t for t in trades if t.get("status") in ("win", "loss", "breakeven")]
    if not closed:
        return {"has_data": False, "message": "No closed paper trades yet."}

    def _wr(subset):
        if not subset: return 0.0
        return round(sum(1 for t in subset if t["status"] == "win") / len(subset) * 100, 1)

    # By strategy
    strats: Dict[str, List] = defaultdict(list)
    for t in closed:
        strats[t.get("strategy", "Unknown") or "Unknown"].append(t)
    strategy_stats = {k: {"trades": len(v), "win_rate": _wr(v)} for k, v in strats.items()}

    # By direction
    longs  = [t for t in closed if t.get("direction") == "long"]
    shorts = [t for t in closed if t.get("direction") == "short"]
    direction_stats = {
        "long":  {"trades": len(longs),  "win_rate": _wr(longs)},
        "short": {"trades": len(shorts), "win_rate": _wr(shorts)},
    }

    # By confidence band (stored in notes "Confidence X%")
    bands: Dict[str, List] = defaultdict(list)
    for t in closed:
        notes = t.get("notes", "") or ""
        conf = 0.65
        try:
            part = [p for p in notes.split("·") if "Confidence" in p]
            if part:
                conf = int(part[0].replace("Confidence", "").replace("%", "").strip()) / 100
        except Exception:
            pass
        bands[_band(conf)].append(t)
    confidence_stats = {k: {"trades": len(v), "win_rate": _wr(v)} for k, v in bands.items()}

    # By reason (TP hit, SL hit, manual)
    reasons: Dict[str, List] = defaultdict(list)
    for t in closed:
        reasons[t.get("reason", "manual") or "manual"].append(t)
    reason_stats = {k: {"count": len(v), "win_rate": _wr(v)} for k, v in reasons.items()}

    # P&L trend (rolling 5-trade average)
    pnl_series = [t.get("pnl_pct", 0) or 0 for t in closed]
    rolling_5 = []
    for i in range(len(pnl_series)):
        window = pnl_series[max(0, i-4): i+1]
        rolling_5.append(round(sum(window) / len(window), 3))

    overall_wr = _wr(closed)
    total_pnl  = round(sum(t.get("pnl_amount", 0) or 0 for t in closed), 2)

    stats = {
        "has_data":         True,
        "total_trades":     len(closed),
        "overall_win_rate": overall_wr,
        "total_pnl":        total_pnl,
        "strategy_stats":   strategy_stats,
        "direction_stats":  direction_stats,
        "confidence_stats": confidence_stats,
        "reason_stats":     reason_stats,
        "pnl_series":       pnl_series,
        "rolling_5":        rolling_5,
    }

    TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)
    TRACKER_FILE.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    return stats
