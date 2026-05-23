"""
Paper Broker — virtual trading account with JSON state persistence.
Simulates order execution at current market price with no slippage model.
"""
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

STATE_FILE = Path(__file__).resolve().parent.parent.parent / "database" / "paper_account.json"
STARTING_BALANCE = 10_000.0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> Dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "balance": STARTING_BALANCE,
        "equity": STARTING_BALANCE,
        "open_positions": [],
        "closed_trades": [],
        "daily_pnl": 0.0,
        "daily_start_balance": STARTING_BALANCE,
        "consecutive_losses": 0,
        "created_at": _now(),
        "last_reset_date": datetime.now(timezone.utc).date().isoformat(),
    }


def _save(state: Dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _daily_reset(state: Dict) -> Dict:
    today = datetime.now(timezone.utc).date().isoformat()
    if state.get("last_reset_date") != today:
        state["daily_pnl"] = 0.0
        state["daily_start_balance"] = state["balance"]
        state["last_reset_date"] = today
    return state


class PaperBroker:
    def __init__(self):
        self._state = _load()
        self._state = _daily_reset(self._state)

    @property
    def balance(self) -> float:
        return self._state["balance"]

    @property
    def equity(self) -> float:
        return self._state["equity"]

    @property
    def daily_pnl(self) -> float:
        return self._state["daily_pnl"]

    @property
    def daily_pnl_pct(self) -> float:
        start = self._state.get("daily_start_balance", STARTING_BALANCE)
        return round(self._state["daily_pnl"] / start * 100, 3) if start else 0.0

    @property
    def consecutive_losses(self) -> int:
        return self._state["consecutive_losses"]

    @property
    def open_positions(self) -> List[Dict]:
        return self._state["open_positions"]

    @property
    def closed_trades(self) -> List[Dict]:
        return self._state["closed_trades"]

    def open_position(self, symbol: str, direction: str, entry: float,
                      sl: float, tp: float, risk_pct: float,
                      strategy: str = "AI Signal", notes: str = "") -> Dict:
        risk_amount = self.balance * risk_pct / 100
        pip_distance = abs(entry - sl)
        units = round(risk_amount / pip_distance, 4) if pip_distance > 0 else 1.0

        pos = {
            "id":        str(uuid.uuid4())[:8],
            "symbol":    symbol,
            "direction": direction,
            "entry":     entry,
            "sl":        sl,
            "tp":        tp,
            "risk_pct":  risk_pct,
            "risk_amount": round(risk_amount, 2),
            "units":     units,
            "strategy":  strategy,
            "notes":     notes,
            "opened_at": _now(),
        }
        self._state["open_positions"].append(pos)
        _save(self._state)
        return pos

    def close_position(self, position_id: str, exit_price: float,
                       reason: str = "manual") -> Optional[Dict]:
        pos = next((p for p in self._state["open_positions"] if p["id"] == position_id), None)
        if pos is None:
            return None

        entry = pos["entry"]
        if pos["direction"] == "long":
            pnl_pct = (exit_price - entry) / entry * 100
        else:
            pnl_pct = (entry - exit_price) / entry * 100

        pnl_amount = round(pos["risk_amount"] * (pnl_pct / (abs(entry - pos["sl"]) / entry * 100 or 1)), 2)
        status = "win" if pnl_amount > 0 else ("loss" if pnl_amount < 0 else "breakeven")

        self._state["balance"] = round(self._state["balance"] + pnl_amount, 2)
        self._state["daily_pnl"] = round(self._state["daily_pnl"] + pnl_amount, 2)
        self._state["equity"] = self._state["balance"]

        if status == "loss":
            self._state["consecutive_losses"] += 1
        else:
            self._state["consecutive_losses"] = 0

        closed = {**pos, "exit": exit_price, "pnl_pct": round(pnl_pct, 3),
                  "pnl_amount": pnl_amount, "status": status,
                  "reason": reason, "closed_at": _now()}

        self._state["open_positions"] = [p for p in self._state["open_positions"] if p["id"] != position_id]
        self._state["closed_trades"].append(closed)
        _save(self._state)
        return closed

    def update_equity(self, current_prices: Dict[str, float]) -> None:
        unrealized = 0.0
        for pos in self._state["open_positions"]:
            price = current_prices.get(pos["symbol"])
            if price is None:
                continue
            entry = pos["entry"]
            if pos["direction"] == "long":
                unreal = (price - entry) / entry * 100 * pos["risk_amount"]
            else:
                unreal = (entry - price) / entry * 100 * pos["risk_amount"]
            unrealized += unreal
        self._state["equity"] = round(self._state["balance"] + unrealized, 2)
        _save(self._state)

    def reset(self) -> None:
        self._state = {
            "balance": STARTING_BALANCE,
            "equity":  STARTING_BALANCE,
            "open_positions": [],
            "closed_trades": [],
            "daily_pnl": 0.0,
            "daily_start_balance": STARTING_BALANCE,
            "consecutive_losses": 0,
            "created_at": _now(),
            "last_reset_date": datetime.now(timezone.utc).date().isoformat(),
        }
        _save(self._state)

    def get_summary(self) -> Dict:
        total_closed = len(self._state["closed_trades"])
        wins   = sum(1 for t in self._state["closed_trades"] if t["status"] == "win")
        losses = sum(1 for t in self._state["closed_trades"] if t["status"] == "loss")
        total_pnl = sum(t["pnl_amount"] for t in self._state["closed_trades"])
        return {
            "balance":            self._state["balance"],
            "equity":             self._state["equity"],
            "starting_balance":   STARTING_BALANCE,
            "total_return_pct":   round((self._state["balance"] - STARTING_BALANCE) / STARTING_BALANCE * 100, 2),
            "daily_pnl":          self._state["daily_pnl"],
            "daily_pnl_pct":      self.daily_pnl_pct,
            "open_positions":     len(self._state["open_positions"]),
            "total_trades":       total_closed,
            "wins":               wins,
            "losses":             losses,
            "win_rate":           round(wins / total_closed * 100, 1) if total_closed else 0.0,
            "total_pnl_amount":   round(total_pnl, 2),
            "consecutive_losses": self._state["consecutive_losses"],
        }
