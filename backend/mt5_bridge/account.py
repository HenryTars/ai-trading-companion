"""Account information from MT5."""

from typing import Optional
from .connector import connector


def get_account_info() -> Optional[dict]:
    """
    Returns account balance, equity, margin, etc.
    Returns None if MT5 is not connected.
    """
    connector.ensure_connected()
    info = connector.account_info()
    if info is None:
        return None

    return {
        "balance":      round(info.balance, 2),
        "equity":       round(info.equity, 2),
        "margin":       round(info.margin, 2),
        "free_margin":  round(info.margin_free, 2),
        "margin_level": round(info.margin_level, 2) if info.margin_level else 0.0,
        "floating_pnl": round(info.profit, 2),
        "currency":     info.currency,
        "leverage":     info.leverage,
        "account_id":   info.login,
        "broker":       info.company,
        "server":       info.server,
    }
