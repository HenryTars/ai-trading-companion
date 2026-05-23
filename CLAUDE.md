# AI Trading Companion — Project Context

## What this project is
A localhost-first AI trading assistant web app built with Streamlit (frontend) + FastAPI (backend).
It analyzes charts, recognizes patterns, provides market insights, and will eventually support autonomous trading with self-improvement.

## Owner
User: Henry Tarsian (henrytarsian@gmail.com)
Built incrementally — confirm each phase before continuing.

---

## How to run

### Python launcher
Python 3.14.2 is installed — use `py` not `python` or `python3`.

### Port situation
- **Port 8501 is blocked** on this Windows machine by a system process (PID 4 / IIS).
- Streamlit runs on **port 8502** instead.
- Access the app at: **http://localhost:8502**
- Backend API runs on port 8000.

### Start commands
```powershell
# Backend (run first in one terminal)
cd C:\Users\Gybrol\AI_Trading_Companion
py -m uvicorn backend.api:app --reload --port 8000

# Frontend (run in a second terminal)
cd C:\Users\Gybrol\AI_Trading_Companion
py -m streamlit run app/main.py --server.port 8502 --server.address localhost
```

Or use the batch file (it auto-detects py vs python):
```
start.bat
```

---

## Tech stack
| Layer | Tech |
|---|---|
| Frontend | Streamlit (dark theme, `#0d1117` bg) |
| Backend | FastAPI + SQLAlchemy 2.0 (async) |
| Database | SQLite via aiosqlite |
| Market data | yfinance |
| Indicators | Custom numpy/pandas (no `ta` lib) |
| Vision | OpenCV headless + Pillow |
| Charts | Plotly |

---

## Project structure
```
AI_Trading_Companion/
├── app/
│   ├── main.py                  # Streamlit entry point, 8-page nav
│   ├── pages/
│   │   ├── dashboard.py         # Live prices, AI signals, watchlist
│   │   ├── chart_analysis.py    # Live chart, AI analysis, setup scorer, screenshot upload
│   │   ├── pattern_recognition.py  # Candlestick + SMC + Classic patterns
│   │   ├── market_insights.py   # Bias engine, multi-TF analysis, global table
│   │   ├── trade_journal.py     # Trade log CRUD
│   │   ├── performance.py       # Stats/metrics
│   │   ├── autonomous_trading.py
│   │   └── settings_page.py
│   └── ui/
│       ├── market_data.py       # get_price_data(), get_market_overview(), SYMBOL_MAP
│       └── components.py        # signal_card(), price_fmt(), section_header()
├── ai_engine/
│   ├── chart_analysis/
│   │   ├── indicators.py        # RSI, MACD, ATR, ADX, BB, Stochastic, EMA
│   │   ├── market_structure.py  # Swing highs/lows, trend, S/R levels
│   │   └── analyzer.py          # analyze_chart() → full dict with bias/confidence/narrative
│   ├── pattern_recognition/
│   │   ├── candlestick.py       # Doji, Hammer, Shooting Star, Engulfing, Marubozu
│   │   ├── smc_patterns.py      # FVG, Order Blocks, BOS (SMC/ICT)
│   │   └── classic_patterns.py  # H&S, Double Top/Bottom, Triangles, Flags, Wedges
│   ├── market_insights/
│   │   ├── bias_engine.py       # generate_bias() wraps analyze_chart + adds scenarios
│   │   └── multi_timeframe.py   # multi_timeframe_analysis() → alignment score
│   ├── strategy_engine/
│   │   └── setup_scorer.py      # score_setup() → A-F grade, R:R, strengths/weaknesses
│   └── vision/
│       └── screenshot_analyzer.py  # OpenCV: trend lines, S/R zones, candle color analysis
├── backend/
│   ├── api.py                   # FastAPI app, WebSocket /ws/price/{symbol}
│   ├── routes/
│   │   ├── journal.py           # Trade CRUD endpoints
│   │   └── analysis.py          # GET /symbol/{symbol}?timeframe=
│   └── services/
│       └── trade_service.py     # DB queries, performance summary
├── database/
│   └── sqlite/
│       └── models.py            # Trade, AnalysisResult, AppSetting, PerformanceSnapshot
├── config/
│   └── settings.py              # Pydantic Settings, reads .env
├── start.bat
└── CLAUDE.md                    # ← this file
```

---

## Key implementation details

### Symbol mapping (yfinance tickers)
| Display | yfinance |
|---|---|
| XAUUSD | GC=F |
| BTCUSDT | BTC-USD |
| EURUSD | EURUSD=X |
| US100 | NQ=F |

### H4 timeframe workaround
yfinance has no H4 interval. We fetch H1 data then resample:
```python
df.resample("4h").agg({"Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"})
```

### Indicator philosophy
All indicators (RSI, MACD, ATR, ADX, Bollinger, Stochastic, EMA) are implemented in pure numpy/pandas in `indicators.py`. No `ta` library — it has no binary wheel for Python 3.14.

### AI confidence scoring
Score 10–95 based on: trend strength + ADX > 25 + RSI alignment + MACD direction + pattern count. Stored as 0.0–1.0 float, displayed as %.

### Dark theme colors
- Background: `#0d1117`
- Card: `#161b22`
- Border: `#30363d`
- Green (bullish): `#238636`
- Red (bearish): `#da3633`
- Blue (accent): `#58a6ff`
- Yellow (warning): `#d29922`

---

## Phases completed

### Phase 1 — Foundation
Config, settings, project structure, database models, SQLite init.

### Phase 2 — Live Dashboard
Streamlit app, dark theme, 8-page navigation, live price strip, candlestick chart, AI signals sidebar, watchlist table.

### Phase 3 — FastAPI Backend
API with lifespan, WebSocket price feed, trade journal routes, analysis routes, CORS for localhost.

### Phase 4 — AI Engine Core
- Indicators: RSI, MACD, ATR, ADX, BB, EMA, Stochastic
- Market structure: swing highs/lows, trend, S/R
- Analyzer: full bias dict with narrative
- Pattern detection: candlestick + SMC (FVG, Order Blocks, BOS)
- Bias engine + multi-timeframe analysis
- Setup scorer (A–F grade)

### Phase 5 — Classic Patterns + Screenshot Vision
- Classic chart patterns: H&S, Inverse H&S, Double Top/Bottom, 3 Triangle types, Bull/Bear Flag, Rising/Falling Wedge
- OpenCV screenshot analyzer: Hough line detection, horizontal S/R morphology, HSV candle color analysis, annotated image output
- Connected upload tab in Chart Analysis page

### Phase 6 — Trade Journal AI
- `ai_engine/trade_journal_ai/trade_reviewer.py` — scores any trade A–F, R:R, strengths/weaknesses, improvement tip
- `ai_engine/trade_journal_ai/habit_detector.py` — detects patterns across all closed trades (session/strategy win rates, R:R habits, risk habits, losing streaks, direction bias)
- `ai_engine/trade_journal_ai/performance_narrator.py` — markdown narrative + 7-day weekly summary
- Trade Journal "AI Review" tab: 4 sub-tabs (single trade review, habit analysis, narrative, weekly)
- Performance page: fully wired with equity curve, breakdown table, pattern performance, AI self-review

---

## Phases remaining

### Phase 7 — Autonomous Trading Engine
- Broker connectors (OANDA, MT5, paper trading mode)
- Execution engine: entry, SL, TP placement
- Risk manager: max drawdown, position sizing, daily limits

### Phase 7 — Autonomous Trading Engine
- Broker connectors (OANDA, MT5, paper trading mode)
- Execution engine: entry, SL, TP placement
- Risk manager: max drawdown, position sizing, daily limits

### Phase 8 — Self-Improvement ML Engine
- Backtesting framework
- Pattern → outcome tracking
- Adaptive optimizer: re-weights which signals matter based on real results

### Phase 9 — Integration & Polish
- Connect all modules end-to-end
- Full test suite
- Performance dashboard with equity curve
- Final UI polish

---

## Known issues / workarounds
- `py` launcher required (not `python`) — Python 3.14.2 installed via Microsoft Store style
- Port 8501 occupied by Windows system (IIS) → use 8502
- Backend CORS set for port 8501 in `backend/api.py` — update to 8502 if running backend simultaneously
- `pandas` installed as `pandas>=2.0.0` (currently 2.3.3) with `--only-binary :all:`
- `ta` library installed separately without `--only-binary` (pure Python)
- PowerShell 5.1: no `&&`, no `?.`, no ternary — use `;` chaining and `if ($?)` checks
