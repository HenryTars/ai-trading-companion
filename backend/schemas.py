from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ── Trade ─────────────────────────────────────────────────────

class TradeCreate(BaseModel):
    symbol:       str
    direction:    str           # long | short
    entry_price:  float
    stop_loss:    float
    take_profit:  float
    risk_percent: float = 1.0
    session:      Optional[str] = None
    strategy:     Optional[str] = None
    notes:        Optional[str] = None


class TradeUpdate(BaseModel):
    status:      Optional[str]   = None    # open | win | loss | breakeven
    exit_price:  Optional[float] = None
    pnl_pips:    Optional[float] = None
    pnl_percent: Optional[float] = None
    notes:       Optional[str]   = None


class TradeResponse(BaseModel):
    id:             int
    symbol:         str
    direction:      str
    entry_price:    float
    stop_loss:      float
    take_profit:    float
    risk_percent:   float
    session:        Optional[str]
    strategy:       Optional[str]
    notes:          Optional[str]
    status:         str
    exit_price:     Optional[float]
    pnl_pips:       Optional[float]
    pnl_percent:    Optional[float]
    ai_score:       Optional[float]
    ai_review:      Optional[str]
    ai_confidence:  Optional[float]
    created_at:     datetime
    closed_at:      Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Analysis ──────────────────────────────────────────────────

class AnalysisCreate(BaseModel):
    symbol:            str
    timeframe:         str
    bias:              str
    confidence:        float
    trend_strength:    Optional[str] = None
    risk_level:        Optional[str] = None
    analysis_text:     Optional[str] = None
    patterns_detected: Optional[str] = None    # JSON string


class AnalysisResponse(AnalysisCreate):
    id:         int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Performance ───────────────────────────────────────────────

class PerformanceSummary(BaseModel):
    total_trades:  int
    wins:          int
    losses:        int
    win_rate:      float
    avg_rr:        float
    total_pnl_pct: float


# ── Settings ──────────────────────────────────────────────────

class SettingUpdate(BaseModel):
    value: str
