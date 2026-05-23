"""
Settings Service — sync read/write for app settings stored in SQLite AppSetting table.
Used by the Streamlit settings page (no async needed).
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from database.sqlite.database import SessionLocal
from database.sqlite.models import AppSetting

DEFAULTS = {
    "trading_mode":           "manual",
    "confidence_threshold":   "0.65",
    "max_risk_pct":           "1.0",
    "max_daily_drawdown":     "3.0",
    "min_rr":                 "1.5",
    "max_consecutive_losses": "3",
    "max_open_positions":     "3",
    "default_timeframe":      "H4",
    "scan_timeframe":         "H4",
    "watchlist":              "XAUUSD,EURUSD,BTCUSDT,GBPUSD,US100",
    "paper_start_balance":    "10000",
}


def get_setting(key: str) -> str:
    db = SessionLocal()
    try:
        row = db.query(AppSetting).filter(AppSetting.key == key).first()
        return row.value if row else DEFAULTS.get(key, "")
    finally:
        db.close()


def set_setting(key: str, value) -> None:
    db = SessionLocal()
    try:
        row = db.query(AppSetting).filter(AppSetting.key == key).first()
        if row:
            row.value = str(value)
        else:
            db.add(AppSetting(key=key, value=str(value)))
        db.commit()
    finally:
        db.close()


def get_all() -> dict:
    db = SessionLocal()
    try:
        rows = db.query(AppSetting).all()
        result = dict(DEFAULTS)
        for row in rows:
            result[row.key] = row.value
        return result
    finally:
        db.close()


def save_all(new_settings: dict) -> None:
    for key, value in new_settings.items():
        set_setting(key, value)


def get_float(key: str) -> float:
    try:
        return float(get_setting(key))
    except (ValueError, TypeError):
        return float(DEFAULTS.get(key, 0))


def get_int(key: str) -> int:
    try:
        return int(float(get_setting(key)))
    except (ValueError, TypeError):
        return int(DEFAULTS.get(key, 0))
