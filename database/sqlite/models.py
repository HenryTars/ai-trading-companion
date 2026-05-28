from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.sql import func
from database.sqlite.database import Base


class Trade(Base):
    __tablename__ = "trades"

    id             = Column(Integer, primary_key=True, index=True)
    symbol         = Column(String(20), nullable=False, index=True)
    direction      = Column(String(10), nullable=False)       # long | short
    entry_price    = Column(Float, nullable=False)
    stop_loss      = Column(Float, nullable=False)
    take_profit    = Column(Float, nullable=False)
    risk_percent   = Column(Float, default=1.0)
    session        = Column(String(20))
    strategy       = Column(String(50))
    notes          = Column(Text)
    status         = Column(String(20), default="open")       # open | win | loss | breakeven
    exit_price     = Column(Float)
    pnl_pips       = Column(Float)
    pnl_percent    = Column(Float)
    screenshot_path= Column(String(500))
    ai_score       = Column(Float)
    ai_review      = Column(Text)
    ai_confidence  = Column(Float)
    created_at     = Column(DateTime, server_default=func.now())
    closed_at      = Column(DateTime)


class MT5Position(Base):
    """Snapshot of an MT5 position (synced from the terminal)."""
    __tablename__ = "mt5_positions"

    id            = Column(Integer, primary_key=True, index=True)
    ticket        = Column(Integer, unique=True, nullable=False, index=True)
    symbol        = Column(String(20), nullable=False)
    direction     = Column(String(10), nullable=False)         # BUY | SELL
    volume        = Column(Float, nullable=False)
    open_price    = Column(Float, nullable=False)
    sl            = Column(Float, default=0.0)
    tp            = Column(Float, default=0.0)
    open_pnl      = Column(Float, default=0.0)
    magic         = Column(Integer, default=0)
    comment       = Column(String(255))
    is_open       = Column(Boolean, default=True)
    opened_at     = Column(DateTime)
    closed_at     = Column(DateTime)
    close_price   = Column(Float)
    final_pnl     = Column(Float)
    synced_at     = Column(DateTime, server_default=func.now(), onupdate=func.now())


class AISignal(Base):
    """AI-generated trading signals."""
    __tablename__ = "ai_signals"

    id            = Column(Integer, primary_key=True, index=True)
    signal_id     = Column(String(50), unique=True, index=True)
    symbol        = Column(String(20), nullable=False, index=True)
    timeframe     = Column(String(10))
    bias          = Column(String(20))                         # bullish | bearish | ranging
    confidence    = Column(Float)
    grade         = Column(String(5))                          # A–F
    entry_low     = Column(Float)
    entry_high    = Column(Float)
    stop_loss     = Column(Float)
    take_profit   = Column(Float)
    risk_reward   = Column(Float)
    narrative     = Column(Text)
    patterns      = Column(Text)                               # JSON list
    status        = Column(String(30), default="active")       # active | approved | rejected | executed | expired
    created_at    = Column(DateTime, server_default=func.now())
    expires_at    = Column(DateTime)


class ExecutionLog(Base):
    """Log of every AI trade execution attempt."""
    __tablename__ = "execution_logs"

    id            = Column(Integer, primary_key=True, index=True)
    signal_id     = Column(String(50), index=True)
    symbol        = Column(String(20))
    action        = Column(String(20))                         # open | close | modify
    direction     = Column(String(10))
    volume        = Column(Float)
    price         = Column(Float)
    sl            = Column(Float)
    tp            = Column(Float)
    mt5_ticket    = Column(Integer)
    success       = Column(Boolean, default=False)
    error_message = Column(Text)
    mode          = Column(String(20))                         # paper | mt5_demo | mt5_live
    created_at    = Column(DateTime, server_default=func.now())


class RiskEvent(Base):
    """Risk rule violations and lock events."""
    __tablename__ = "risk_events"

    id            = Column(Integer, primary_key=True, index=True)
    event_type    = Column(String(50))                         # daily_drawdown | consecutive_loss | etc.
    description   = Column(Text)
    value         = Column(Float)
    threshold     = Column(Float)
    resolved      = Column(Boolean, default=False)
    created_at    = Column(DateTime, server_default=func.now())


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id                = Column(Integer, primary_key=True, index=True)
    symbol            = Column(String(20), nullable=False, index=True)
    timeframe         = Column(String(10), nullable=False)
    bias              = Column(String(20))
    confidence        = Column(Float)
    trend_strength    = Column(String(20))
    risk_level        = Column(String(20))
    analysis_text     = Column(Text)
    patterns_detected = Column(Text)
    created_at        = Column(DateTime, server_default=func.now())


class AppSetting(Base):
    __tablename__ = "app_settings"

    key        = Column(String(100), primary_key=True)
    value      = Column(Text)
    updated_at = Column(DateTime, server_default=func.now())


class PerformanceSnapshot(Base):
    __tablename__ = "performance_snapshots"

    id             = Column(Integer, primary_key=True, index=True)
    date           = Column(String(20), index=True)
    total_trades   = Column(Integer, default=0)
    wins           = Column(Integer, default=0)
    losses         = Column(Integer, default=0)
    win_rate       = Column(Float, default=0.0)
    avg_rr         = Column(Float, default=0.0)
    total_pnl_pct  = Column(Float, default=0.0)
    max_drawdown   = Column(Float, default=0.0)
    created_at     = Column(DateTime, server_default=func.now())
