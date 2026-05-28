"""
MT5 bridge — connects to the local MetaTrader 5 terminal.

Falls back gracefully when the MetaTrader5 package is not installed
or the terminal is not running, so the rest of the app still works.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# ── Try importing the package ─────────────────────────────────────────────────

try:
    import MetaTrader5 as _mt5
    _MT5_AVAILABLE = True
except ImportError:
    _mt5 = None  # type: ignore
    _MT5_AVAILABLE = False
    logger.warning("MetaTrader5 package not installed. Run: pip install MetaTrader5")


@dataclass
class MT5ConnectionStatus:
    connected: bool = False
    reason: str = ""
    account_id: int = 0
    broker: str = ""
    server: str = ""
    last_checked: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class MT5Connector:
    """Singleton-style wrapper around the MetaTrader5 package."""

    def __init__(self) -> None:
        self._connected = False
        self._status = MT5ConnectionStatus(
            connected=False,
            reason="Not initialised" if _MT5_AVAILABLE else "MetaTrader5 package not installed",
        )

    # ── Public API ─────────────────────────────────────────────────────────

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def status(self) -> MT5ConnectionStatus:
        self._status.last_checked = datetime.utcnow().isoformat()
        return self._status

    def connect(self) -> MT5ConnectionStatus:
        if not _MT5_AVAILABLE:
            return self._build_status(False, "MetaTrader5 package not installed. Run: pip install MetaTrader5")

        try:
            if not _mt5.initialize():
                code, msg = _mt5.last_error()
                return self._build_status(False, f"MT5 init failed ({code}): {msg}")

            info = _mt5.account_info()
            if info is None:
                return self._build_status(False, "Connected but could not read account info")

            self._connected = True
            self._status = MT5ConnectionStatus(
                connected=True,
                reason="",
                account_id=info.login,
                broker=info.company,
                server=info.server,
            )
            logger.info("MT5 connected — account %s @ %s", info.login, info.server)
            return self._status

        except Exception as exc:
            return self._build_status(False, str(exc))

    def disconnect(self) -> None:
        if _MT5_AVAILABLE:
            try:
                _mt5.shutdown()
            except Exception:
                pass
        self._connected = False
        self._status = MT5ConnectionStatus(connected=False, reason="Disconnected by user")

    def ensure_connected(self) -> bool:
        """Re-connect if the terminal dropped. Returns True if connected."""
        if not self._connected:
            self.connect()
        elif _MT5_AVAILABLE:
            # Ping: try reading terminal info
            try:
                ti = _mt5.terminal_info()
                if ti is None:
                    self._connected = False
                    self.connect()
            except Exception:
                self._connected = False
                self.connect()
        return self._connected

    # ── Raw MT5 access (only when connected) ──────────────────────────────

    def account_info(self):
        if not (self._connected and _MT5_AVAILABLE):
            return None
        return _mt5.account_info()

    def positions_get(self, **kwargs):
        if not (self._connected and _MT5_AVAILABLE):
            return []
        result = _mt5.positions_get(**kwargs)
        return list(result) if result else []

    def history_deals_get(self, date_from, date_to, **kwargs):
        if not (self._connected and _MT5_AVAILABLE):
            return []
        result = _mt5.history_deals_get(date_from, date_to, **kwargs)
        return list(result) if result else []

    def order_send(self, request: dict):
        if not (self._connected and _MT5_AVAILABLE):
            return None
        return _mt5.order_send(request)

    def symbol_info_tick(self, symbol: str):
        if not (self._connected and _MT5_AVAILABLE):
            return None
        return _mt5.symbol_info_tick(symbol)

    def copy_rates_from_pos(self, symbol: str, timeframe, start: int, count: int):
        if not (self._connected and _MT5_AVAILABLE):
            return None
        return _mt5.copy_rates_from_pos(symbol, timeframe, start, count)

    # ── Helpers ────────────────────────────────────────────────────────────

    def _build_status(self, connected: bool, reason: str) -> MT5ConnectionStatus:
        self._connected = connected
        self._status = MT5ConnectionStatus(connected=connected, reason=reason)
        return self._status


# Global singleton
connector = MT5Connector()
