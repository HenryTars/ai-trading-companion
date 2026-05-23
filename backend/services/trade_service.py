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
