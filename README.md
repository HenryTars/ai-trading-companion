# AI Trading Companion

An AI-powered trading companion web application — runs locally on `localhost`.

## Quick Start

### 1. Install Python 3.10+
Download from https://python.org — check "Add to PATH" during install.

### 2. Install dependencies
Open a terminal in this folder and run:

```
pip install -r requirements.txt
```

### 3. Configure environment (optional)
```
copy .env.example .env
```
Edit `.env` to add your broker API keys.

### 4. Start the application

**Option A — Double-click:**
```
start.bat
```

**Option B — Manual (two terminals):**

Terminal 1 — Backend:
```
uvicorn backend.api:app --host 127.0.0.1 --port 8000 --reload
```

Terminal 2 — Frontend:
```
streamlit run app/main.py --server.port 8501
```

### 5. Open in browser
- **App:**      http://localhost:8501
- **API:**      http://localhost:8000
- **API Docs:** http://localhost:8000/docs

---

## Project Structure

```
AI_Trading_Companion/
├── app/                    Streamlit frontend
│   ├── main.py             App entry point + navigation
│   └── pages/              One file per page
├── backend/                FastAPI backend
│   ├── api.py              API entry point
│   └── routes/             Route handlers
├── ai_engine/              AI analysis modules (Phase 5)
├── autonomous_trading/     Autonomous execution (Phase 8)
├── database/sqlite/        SQLite database (Phase 4)
├── uploads/                User-uploaded chart images
├── models/                 Trained ML models
├── logs/                   Application logs
├── config/settings.py      Central configuration
├── requirements.txt        Python dependencies
└── start.bat               Windows one-click launcher
```

---

## Build Phases

| Phase | Status | Description |
|-------|--------|-------------|
| 1 | COMPLETE | Foundation, folder structure, skeleton UI/API |
| 2 | Next | Streamlit dashboard with live UI components |
| 3 | Planned | FastAPI backend with real services |
| 4 | Planned | SQLite database + ORM models |
| 5 | Planned | AI engine — chart analysis, patterns, insights |
| 6 | Planned | Screenshot analysis (OpenCV) |
| 7 | Planned | Trade journal + AI review |
| 8 | Planned | Autonomous trading engine + broker connectors |
| 9 | Planned | Self-improvement ML + backtesting |
| 10 | Planned | Integration, testing, polish |

---

## Trading Modes

| Mode | Description |
|------|-------------|
| Manual | AI analyzes only — no execution |
| Assisted | AI generates setups — you approve/reject |
| Autonomous | AI executes trades automatically |

Set in `.env`:  `TRADING_MODE=manual`

---

## Safety

- Default mode is **Manual** — no trades are executed automatically
- Autonomous mode requires explicit configuration and broker connection
- Built-in risk controls: max drawdown, max risk per trade, emergency shutdown
