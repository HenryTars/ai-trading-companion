"""
AI Risk Manager
Enforces all risk rules before any trade is executed.
Returns (allowed: bool, reason: str).
"""
from typing import Dict, Tuple


class RiskManager:
    def __init__(self,
                 max_risk_pct: float = 1.0,
                 max_daily_drawdown_pct: float = 3.0,
                 max_consecutive_losses: int = 3,
                 max_open_positions: int = 3,
                 min_rr: float = 1.5,
                 min_confidence: float = 0.60):
        self.max_risk_pct           = max_risk_pct
        self.max_daily_drawdown_pct = max_daily_drawdown_pct
        self.max_consecutive_losses = max_consecutive_losses
        self.max_open_positions     = max_open_positions
        self.min_rr                 = min_rr
        self.min_confidence         = min_confidence

    def check(self, signal: Dict, broker_summary: Dict) -> Tuple[bool, str]:
        """
        signal keys: symbol, direction, confidence, entry, sl, tp, rr
        broker_summary keys: daily_pnl_pct, consecutive_losses, open_positions, balance
        """
        # 1. Daily drawdown hard stop
        daily_dd = broker_summary.get("daily_pnl_pct", 0)
        if daily_dd <= -self.max_daily_drawdown_pct:
            return False, f"Daily drawdown limit hit ({daily_dd:.2f}%) — trading paused for today"

        # 2. Consecutive losses
        consec = broker_summary.get("consecutive_losses", 0)
        if consec >= self.max_consecutive_losses:
            return False, f"{consec} consecutive losses — cool-down required before next trade"

        # 3. Open positions cap
        open_pos = broker_summary.get("open_positions", 0)
        if open_pos >= self.max_open_positions:
            return False, f"Max open positions ({self.max_open_positions}) reached"

        # 4. Minimum R:R
        rr = signal.get("rr", 0)
        if rr < self.min_rr:
            return False, f"R:R {rr:.2f} below minimum {self.min_rr} — setup rejected"

        # 5. Minimum AI confidence
        conf = signal.get("confidence", 0)
        if conf < self.min_confidence:
            return False, f"AI confidence {int(conf*100)}% below threshold {int(self.min_confidence*100)}%"

        # 6. Risk per trade
        risk_pct = signal.get("risk_pct", self.max_risk_pct)
        if risk_pct > self.max_risk_pct:
            return False, f"Requested risk {risk_pct}% exceeds max {self.max_risk_pct}%"

        # 7. Positive balance
        if broker_summary.get("balance", 0) <= 0:
            return False, "Account balance depleted — trading halted"

        return True, "All risk checks passed"

    def get_position_size_pct(self, signal: Dict) -> float:
        """Returns the risk % to use (capped at max)."""
        return min(signal.get("risk_pct", self.max_risk_pct), self.max_risk_pct)
