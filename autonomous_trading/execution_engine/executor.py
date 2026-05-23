"""
Execution Engine
Orchestrates: scan signals → risk check → execute on paper broker.
"""
from typing import Dict, List, Tuple
from autonomous_trading.broker_connector.paper_broker import PaperBroker
from autonomous_trading.ai_risk_manager.risk_manager import RiskManager
from autonomous_trading.strategy_selector.signal_generator import scan_signals


class TradingExecutor:
    def __init__(self, risk_manager: RiskManager = None):
        self.broker = PaperBroker()
        self.rm     = risk_manager or RiskManager()

    def scan_and_execute(self, symbols: List[str] = None,
                         timeframe: str = "H4",
                         dry_run: bool = False) -> List[Dict]:
        """
        Scan symbols → filter through risk manager → execute survivors.
        dry_run=True: return signals without actually opening positions.
        Returns list of execution results.
        """
        signals = scan_signals(symbols, timeframe)
        summary = self.broker.get_summary()
        results = []

        for sig in signals:
            allowed, reason = self.rm.check(sig, summary)
            result = {
                "symbol":    sig["symbol"],
                "direction": sig["direction"],
                "confidence": sig["confidence"],
                "rr":         sig["rr"],
                "entry":      sig["entry"],
                "sl":         sig["sl"],
                "tp":         sig["tp"],
                "allowed":    allowed,
                "reason":     reason,
                "executed":   False,
                "position_id": None,
            }

            if allowed and not dry_run:
                risk_pct = self.rm.get_position_size_pct(sig)
                pos = self.broker.open_position(
                    symbol    = sig["symbol"],
                    direction = sig["direction"],
                    entry     = sig["entry"],
                    sl        = sig["sl"],
                    tp        = sig["tp"],
                    risk_pct  = risk_pct,
                    strategy  = f"AI {sig['timeframe']} Signal",
                    notes     = f"Confidence {int(sig['confidence']*100)}% · R:R {sig['rr']}",
                )
                result["executed"]    = True
                result["position_id"] = pos["id"]
                result["risk_pct"]    = risk_pct
                summary = self.broker.get_summary()

            results.append(result)

        return results

    def close_position(self, position_id: str, exit_price: float,
                       reason: str = "manual") -> Dict:
        closed = self.broker.close_position(position_id, exit_price, reason)
        return closed or {}

    def check_auto_close(self, current_prices: Dict[str, float]) -> List[Dict]:
        """
        Check each open position against current price for SL/TP hits.
        Returns list of auto-closed trade results.
        """
        self.broker.update_equity(current_prices)
        closed_results = []

        for pos in list(self.broker.open_positions):
            price = current_prices.get(pos["symbol"])
            if price is None:
                continue

            hit_tp = hit_sl = False
            if pos["direction"] == "long":
                if price >= pos["tp"]:  hit_tp = True
                if price <= pos["sl"]:  hit_sl = True
            else:
                if price <= pos["tp"]:  hit_tp = True
                if price >= pos["sl"]:  hit_sl = True

            if hit_tp or hit_sl:
                reason = "TP hit" if hit_tp else "SL hit"
                closed = self.broker.close_position(pos["id"], price, reason)
                if closed:
                    closed_results.append(closed)

        return closed_results

    def get_status(self) -> Dict:
        return self.broker.get_summary()
