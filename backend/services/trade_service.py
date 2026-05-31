from datetime import datetime
from sqlalchemy.orm import Session
from database.sqlite.models import Trade
from backend.schemas import TradeCreate, TradeUpdate


def create_trade(db: Session, trade: TradeCreate) -> Trade:
    db_trade = Trade(**trade.model_dump())
    db.add(db_trade)
    db.commit()
    db.refresh(db_trade)
    return db_trade


def get_trade(db: Session, trade_id: int) -> Trade | None:
    return db.query(Trade).filter(Trade.id == trade_id).first()


def get_trades(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    symbol: str | None = None,
    status: str | None = None,
) -> list[Trade]:
    q = db.query(Trade)
    if symbol:
        q = q.filter(Trade.symbol == symbol.upper())
    if status:
        q = q.filter(Trade.status == status)
    return q.order_by(Trade.created_at.desc()).offset(skip).limit(limit).all()


def update_trade(db: Session, trade_id: int, update: TradeUpdate) -> Trade | None:
    trade = get_trade(db, trade_id)
    if not trade:
        return None
    for key, val in update.model_dump(exclude_none=True).items():
        setattr(trade, key, val)
    if update.status in ("win", "loss", "breakeven"):
        trade.closed_at = datetime.utcnow()
    db.commit()
    db.refresh(trade)
    return trade


def delete_trade(db: Session, trade_id: int) -> bool:
    trade = get_trade(db, trade_id)
    if not trade:
        return False
    db.delete(trade)
    db.commit()
    return True


def get_performance_summary(db: Session) -> dict:
    closed = db.query(Trade).filter(Trade.status != "open").all()
    if not closed:
        return {
            "total_trades": 0, "wins": 0, "losses": 0,
            "win_rate": 0.0, "avg_rr": 0.0, "total_pnl_pct": 0.0,
        }
    wins   = sum(1 for t in closed if t.status == "win")
    losses = sum(1 for t in closed if t.status == "loss")
    total  = len(closed)
    pnl_values = [t.pnl_percent for t in closed if t.pnl_percent is not None]
    total_pnl  = sum(pnl_values)
    rr_vals = []
    for t in closed:
        risk   = abs(t.entry_price - t.stop_loss)
        reward = abs(t.take_profit - t.entry_price)
        if risk > 0:
            rr_vals.append(reward / risk)
    avg_rr = sum(rr_vals) / len(rr_vals) if rr_vals else 0.0
    return {
        "total_trades":  total,
        "wins":          wins,
        "losses":        losses,
        "win_rate":      round(wins / total * 100, 2),
        "avg_rr":        round(avg_rr, 2),
        "total_pnl_pct": round(total_pnl, 2),
    }


def get_analytics(db: Session) -> dict:
    all_trades  = db.query(Trade).order_by(Trade.created_at.asc()).all()
    closed      = [t for t in all_trades if t.status != "open"]
    open_trades = [t for t in all_trades if t.status == "open"]

    wins      = [t for t in closed if t.status == "win"]
    losses    = [t for t in closed if t.status == "loss"]
    breakeven = [t for t in closed if t.status == "breakeven"]

    pnl_vals  = [t.pnl_percent for t in closed if t.pnl_percent is not None]
    win_pnls  = [t.pnl_percent for t in wins   if t.pnl_percent is not None]
    loss_pnls = [t.pnl_percent for t in losses if t.pnl_percent is not None]
    total_pnl = sum(pnl_vals)

    # Avg R:R across all trades
    rr_vals = []
    for t in all_trades:
        risk   = abs(t.entry_price - t.stop_loss)
        reward = abs(t.take_profit - t.entry_price)
        if risk > 0:
            rr_vals.append(reward / risk)
    avg_rr = sum(rr_vals) / len(rr_vals) if rr_vals else 0.0

    # Profit factor
    gross_wins   = sum(p for p in win_pnls  if p > 0)
    gross_losses = abs(sum(p for p in loss_pnls if p < 0))
    profit_factor = round(gross_wins / gross_losses, 2) if gross_losses > 0 else 0.0

    # Max drawdown (peak-to-trough on cumulative P&L)
    cum, peak, max_dd = 0.0, 0.0, 0.0
    for t in closed:
        if t.pnl_percent is not None:
            cum  += t.pnl_percent
            peak  = max(peak, cum)
            max_dd = max(max_dd, peak - cum)

    # Current streak
    streak_type: str | None = None
    streak_count = 0
    for t in reversed(closed):
        if streak_type is None:
            streak_type  = t.status
            streak_count = 1
        elif t.status == streak_type:
            streak_count += 1
        else:
            break

    # Equity curve — cumulative P&L over time
    cum = 0.0
    equity_curve = []
    for t in closed:
        if t.pnl_percent is not None:
            cum += t.pnl_percent
            ref  = t.closed_at or t.created_at
            equity_curve.append({
                "time":  ref.strftime("%Y-%m-%d"),
                "value": round(cum, 3),
            })

    # ── Breakdowns ────────────────────────────────────────────────────────────

    def _breakdown(key_fn, label_key: str) -> list[dict]:
        m: dict[str, dict] = {}
        for t in all_trades:
            k = key_fn(t) or "Unknown"
            if k not in m:
                m[k] = {label_key: k, "trades": 0, "wins": 0, "losses": 0,
                         "pnl_sum": 0.0, "rr_sum": 0.0, "rr_n": 0}
            m[k]["trades"] += 1
            if t.status == "win":    m[k]["wins"]   += 1
            if t.status == "loss":   m[k]["losses"] += 1
            if t.pnl_percent:        m[k]["pnl_sum"] += t.pnl_percent
            risk   = abs(t.entry_price - t.stop_loss)
            reward = abs(t.take_profit - t.entry_price)
            if risk > 0:
                m[k]["rr_sum"] += reward / risk
                m[k]["rr_n"]   += 1

        result = []
        for v in m.values():
            closed_n = v["wins"] + v["losses"]
            result.append({
                label_key:  v[label_key],
                "trades":   v["trades"],
                "wins":     v["wins"],
                "losses":   v["losses"],
                "win_rate": round(v["wins"] / closed_n * 100, 1) if closed_n > 0 else 0.0,
                "pnl_pct":  round(v["pnl_sum"], 2),
                "avg_rr":   round(v["rr_sum"] / v["rr_n"], 2) if v["rr_n"] > 0 else 0.0,
            })
        return sorted(result, key=lambda x: x["trades"], reverse=True)

    return {
        "summary": {
            "total_trades":  len(all_trades),
            "closed_trades": len(closed),
            "open_trades":   len(open_trades),
            "wins":          len(wins),
            "losses":        len(losses),
            "breakeven":     len(breakeven),
            "win_rate":      round(len(wins) / len(closed) * 100, 2) if closed else 0.0,
            "avg_rr":        round(avg_rr, 2),
            "total_pnl_pct": round(total_pnl, 2),
            "profit_factor": profit_factor,
            "max_drawdown":  round(-max_dd, 2),
            "best_trade":    round(max(pnl_vals), 2) if pnl_vals else 0.0,
            "worst_trade":   round(min(pnl_vals), 2) if pnl_vals else 0.0,
            "avg_win_pct":   round(sum(win_pnls)  / len(win_pnls),  2) if win_pnls  else 0.0,
            "avg_loss_pct":  round(sum(loss_pnls) / len(loss_pnls), 2) if loss_pnls else 0.0,
            "streak": {"type": streak_type, "count": streak_count} if streak_type else None,
        },
        "equity_curve": equity_curve,
        "by_symbol":   _breakdown(lambda t: t.symbol,   "symbol"),
        "by_session":  _breakdown(lambda t: t.session,  "session"),
        "by_strategy": _breakdown(lambda t: t.strategy, "strategy"),
    }
