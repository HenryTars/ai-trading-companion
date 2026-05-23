from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from database.sqlite.database import Base


class Trade(Base):
    __tablename__ = "trades"

    id            = Column(Integer, primary_key=True, index=True)
    symbol        = Column(String(20), nullable=False, index=True)
    direction     = Column(String(10), nullable=False)      # long | short
    entry_price   = Column(Float, nullable=False)
    stop_loss     = Column(Float, nullable=False)
    take_profit   = Column(Float, nullable=False)
    risk_percent  = Column(Float, default=1.0)
    session       = Column(String(20))                      # London | New York | Asian | Other
    strategy      = Column(String(50))
    notes         = Column(Text)

    # Outcome — filled when trade is closed
    status        = Column(String(20), default="open")      # open | win | loss | breakeven
    exit_price    = Column(Float)
    pnl_pips      = Column(Float)
    pnl_percent   = Column(Float)

    # AI fields — filled by AI engine (Phase 5+)
    screenshot_path = Column(String(500))
    ai_score        = Column(Float)                         # 0–100
    ai_review       = Column(Text)
    ai_confidence   = Column(Float)                         # 0.0–1.0

    created_at    = Column(DateTime, server_default=func.now())
    closed_at     = Column(DateTime)


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id               = Column(Integer, primary_key=True, index=True)
    symbol           = Column(String(20), nullable=False, index=True)
    timeframe        = Column(String(10), nullable=False)
    bias             = Column(String(20))           # bullish | bearish | ranging
    confidence       = Column(Float)                # 0.0–1.0
    trend_strength   = Column(String(20))           # strong | moderate | weak
    risk_level       = Column(String(20))           # low | medium | high
    analysis_text    = Column(Text)
    patterns_detected = Column(Text)                # JSON string
    created_at       = Column(DateTime, server_default=func.now())


class AppSetting(Base):
    __tablename__ = "app_settings"

    key        = Column(String(100), primary_key=True)
    value      = Column(Text)
    updated_at = Column(DateTime, server_default=func.now())


class PerformanceSnapshot(Base):
    __tablename__ = "performance_snapshots"

    id           = Column(Integer, primary_key=True, index=True)
    date         = Column(String(20), index=True)   # YYYY-MM-DD
    total_trades = Column(Integer, default=0)
    wins         = Column(Integer, default=0)
    losses       = Column(Integer, default=0)
    win_rate     = Column(Float, default=0.0)
    avg_rr       = Column(Float, default=0.0)
    total_pnl_pct = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    created_at   = Column(DateTime, server_default=func.now())
