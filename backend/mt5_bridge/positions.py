"""Open positions and order execution via MT5."""

import logging
from datetime import datetime, timezone
from typing import Optional
from .connector import connector

logger = logging.getLogger(__name__)

try:
    import MetaTrader5 as _mt5_module
    _ORDER_TYPE_BUY  = _mt5_module.ORDER_TYPE_BUY
    _ORDER_TYPE_SELL = _mt5_module.ORDER_TYPE_SELL
    _TRADE_ACTION_DEAL   = _mt5_module.TRADE_ACTION_DEAL
    _TRADE_ACTION_SLTP   = _mt5_module.TRADE_ACTION_SLTP
    _ORDER_TIME_GTC      = _mt5_module.ORDER_TIME_GTC
    _ORDER_FILLING_IOC   = _mt5_module.ORDER_FILLING_IOC
    _DEAL_ENTRY_IN       = _mt5_module.DEAL_ENTRY_IN
    _DEAL_ENTRY_OUT      = _mt5_module.DEAL_ENTRY_OUT
    _POSITION_TYPE_BUY   = _mt5_module.POSITION_TYPE_BUY
except Exception:
    # placeholders — only used when MT5 is actually available
    _ORDER_TYPE_BUY = 0
    _ORDER_TYPE_SELL = 1
    _TRADE_ACTION_DEAL = 1
    _TRADE_ACTION_SLTP = 6
    _ORDER_TIME_GTC = 1
    _ORDER_FILLING_IOC = 1
    _DEAL_ENTRY_IN = 0
    _DEAL_ENTRY_OUT = 1
    _POSITION_TYPE_BUY = 0


def _pos_to_dict(pos) -> dict:
    ptype = "BUY" if pos.type == _POSITION_TYPE_BUY else "SELL"
    return {
        "ticket":        pos.ticket,
        "symbol":        pos.symbol,
        "type":          ptype,
        "volume":        pos.volume,
        "open_price":    round(pos.price_open, 5),
        "current_price": round(pos.price_current, 5),
        "sl":            round(pos.sl, 5),
        "tp":            round(pos.tp, 5),
        "pnl":           round(pos.profit, 2),
        "pips":          round((pos.price_current - pos.price_open) * (1 if ptype == "BUY" else -1) * 10000, 1),
        "swap":          round(pos.swap, 2),
        "open_time":     datetime.fromtimestamp(pos.time, tz=timezone.utc).isoformat(),
        "magic":         pos.magic,
        "comment":       pos.comment,
    }


def get_open_positions(symbol: Optional[str] = None) -> list[dict]:
    connector.ensure_connected()
    kwargs = {"symbol": symbol} if symbol else {}
    raw = connector.positions_get(**kwargs)
    return [_pos_to_dict(p) for p in raw]


def close_position(ticket: int) -> dict:
    """
    Close an open position by ticket.
    Returns result dict with 'success' and optional 'error'.
    """
    connector.ensure_connected()
    if not connector.is_connected:
        return {"success": False, "error": "MT5 not connected"}

    positions = connector.positions_get()
    pos = next((p for p in positions if p.ticket == ticket), None)
    if pos is None:
        return {"success": False, "error": f"Ticket {ticket} not found"}

    tick = connector.symbol_info_tick(pos.symbol)
    if tick is None:
        return {"success": False, "error": f"Cannot get tick for {pos.symbol}"}

    close_type  = _ORDER_TYPE_SELL if pos.type == _POSITION_TYPE_BUY else _ORDER_TYPE_BUY
    close_price = tick.bid if pos.type == _POSITION_TYPE_BUY else tick.ask

    request = {
        "action":    _TRADE_ACTION_DEAL,
        "position":  ticket,
        "symbol":    pos.symbol,
        "volume":    pos.volume,
        "type":      close_type,
        "price":     close_price,
        "deviation": 20,
        "magic":     pos.magic,
        "comment":   "AI close",
        "type_time": _ORDER_TIME_GTC,
        "type_filling": _ORDER_FILLING_IOC,
    }

    result = connector.order_send(request)
    if result is None:
        return {"success": False, "error": "order_send returned None"}

    if result.retcode == 10009:  # TRADE_RETCODE_DONE
        logger.info("Closed ticket %s, profit=%.2f", ticket, result.profit)
        return {"success": True, "ticket": ticket, "profit": round(result.profit, 2)}

    return {"success": False, "error": f"retcode={result.retcode}: {result.comment}"}


def open_position(
    symbol: str,
    direction: str,   # "BUY" | "SELL"
    volume: float,
    sl: float = 0.0,
    tp: float = 0.0,
    magic: int = 20250001,
    comment: str = "AI trade",
) -> dict:
    """Open a market order. Returns result dict."""
    connector.ensure_connected()
    if not connector.is_connected:
        return {"success": False, "error": "MT5 not connected"}

    tick = connector.symbol_info_tick(symbol)
    if tick is None:
        return {"success": False, "error": f"Cannot get tick for {symbol}"}

    order_type = _ORDER_TYPE_BUY if direction.upper() == "BUY" else _ORDER_TYPE_SELL
    price = tick.ask if direction.upper() == "BUY" else tick.bid

    request = {
        "action":    _TRADE_ACTION_DEAL,
        "symbol":    symbol,
        "volume":    volume,
        "type":      order_type,
        "price":     price,
        "sl":        sl,
        "tp":        tp,
        "deviation": 20,
        "magic":     magic,
        "comment":   comment,
        "type_time": _ORDER_TIME_GTC,
        "type_filling": _ORDER_FILLING_IOC,
    }

    result = connector.order_send(request)
    if result is None:
        return {"success": False, "error": "order_send returned None"}

    if result.retcode == 10009:
        logger.info("Opened %s %s %.2f @ %.5f", direction, symbol, volume, result.price)
        return {"success": True, "ticket": result.order, "price": result.price}

    return {"success": False, "error": f"retcode={result.retcode}: {result.comment}"}


def get_history(limit: int = 50) -> list[dict]:
    """Recent closed deals."""
    from datetime import timedelta
    connector.ensure_connected()
    if not connector.is_connected:
        return []

    date_to   = datetime.now(tz=timezone.utc)
    date_from = date_to - timedelta(days=30)
    deals = connector.history_deals_get(date_from, date_to)

    result = []
    for d in deals[-limit:]:
        result.append({
            "ticket":  d.ticket,
            "order":   d.order,
            "symbol":  d.symbol,
            "type":    "IN" if d.entry == _DEAL_ENTRY_IN else "OUT",
            "volume":  d.volume,
            "price":   round(d.price, 5),
            "profit":  round(d.profit, 2),
            "swap":    round(d.swap, 2),
            "commission": round(d.commission, 2),
            "time":    datetime.fromtimestamp(d.time, tz=timezone.utc).isoformat(),
            "comment": d.comment,
        })
    return result
