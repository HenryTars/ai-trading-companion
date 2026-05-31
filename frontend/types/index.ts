// ─── MT5 / Account ───────────────────────────────────────────────────────────

export interface MT5Status {
  connected: boolean;
  reason?: string;
  account_id?: number;
  broker?: string;
  server?: string;
  last_checked?: string;
}

export interface AccountInfo {
  balance: number;
  equity: number;
  margin: number;
  free_margin: number;
  margin_level: number;
  floating_pnl: number;
  currency: string;
  leverage: number;
  account_id: number;
  broker: string;
  server: string;
}

export interface MT5Position {
  ticket: number;
  symbol: string;
  type: "BUY" | "SELL";
  volume: number;
  open_price: number;
  current_price: number;
  sl: number;
  tp: number;
  pnl: number;
  pips: number;
  swap: number;
  open_time: string;
  magic: number;
  comment: string;
}

export interface MT5HistoryDeal {
  ticket: number;
  order: number;
  symbol: string;
  type: string;
  volume: number;
  price: number;
  profit: number;
  swap: number;
  commission: number;
  time: string;
  comment: string;
}

// ─── Market Data ─────────────────────────────────────────────────────────────

export interface PriceTick {
  symbol: string;
  bid: number;
  ask: number;
  spread: number;
  timestamp: string;
}

export interface OHLCV {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface WatchlistItem {
  symbol: string;
  display: string;
  bid: number;
  ask: number;
  change: number;
  change_pct: number;
  spread: number;
  session: string;
}

// ─── AI Engine ───────────────────────────────────────────────────────────────

export type Bias = "bullish" | "bearish" | "ranging";
export type TrendStrength = "strong" | "moderate" | "weak";
export type RiskLevel = "low" | "medium" | "high";
export type SignalGrade = "A" | "B" | "C" | "D" | "F";

export interface AISignal {
  id: string;
  symbol: string;
  timeframe: string;
  bias: Bias;
  confidence: number;
  grade: SignalGrade;
  entry_zone: [number, number];
  stop_loss: number;
  take_profit: number;
  risk_reward: number;
  narrative: string;
  patterns: string[];
  created_at: string;
  expires_at?: string;
}

export interface MarketAnalysis {
  symbol: string;
  timeframe: string;
  bias: Bias;
  confidence: number;
  trend_strength: TrendStrength;
  risk_level: RiskLevel;
  narrative: string;
  patterns_detected: string[];
  key_levels: number[];
  indicators: {
    rsi: number;
    macd_signal: string;
    adx: number;
    atr: number;
  };
  created_at: string;
}

// ─── Trade Journal ────────────────────────────────────────────────────────────

export type TradeStatus = "open" | "win" | "loss" | "breakeven";
export type TradeDirection = "long" | "short";

export interface Trade {
  id: number;
  symbol: string;
  direction: TradeDirection;
  entry_price: number;
  stop_loss: number;
  take_profit: number;
  risk_percent: number;
  session?: string;
  strategy?: string;
  notes?: string;
  status: TradeStatus;
  exit_price?: number;
  pnl_pips?: number;
  pnl_percent?: number;
  ai_score?: number;
  ai_confidence?: number;
  screenshot_path?: string;
  created_at: string;
  closed_at?: string;
}

// ─── System Status ────────────────────────────────────────────────────────────

export interface SystemStatus {
  backend: boolean;
  mt5: boolean;
  database: boolean;
  ai_engine: boolean;
  version: string;
  uptime: number;
  trading_mode: string;
}

// ─── Risk ─────────────────────────────────────────────────────────────────────

export interface RiskState {
  daily_pnl: number;
  daily_trades: number;
  open_trades: number;
  consecutive_losses: number;
  is_locked: boolean;
  lock_reason?: string;
  daily_drawdown_pct: number;
  available_risk: number;
}

// ─── Autonomous Trading ───────────────────────────────────────────────────────

export type TradingMode = "manual" | "assisted" | "semi_auto" | "full_auto";

export interface AutoTradingConfig {
  mode: TradingMode;
  symbols: string[];
  max_risk_pct: number;
  volume: number;
  max_open_trades: number;
  max_daily_trades: number;
  min_confidence: number;
  min_rr: number;
  use_trailing_stop: boolean;
  cooldown_minutes: number;
  max_daily_drawdown: number;
}

export interface PendingSignal {
  signal: AISignal;
  status: "pending_approval" | "approved" | "rejected" | "executed" | "expired";
  created_at: string;
}
