import axios from "axios";
import type {
  AccountInfo,
  MT5Status,
  MT5Position,
  SystemStatus,
  MarketAnalysis,
  Trade,
  AISignal,
  RiskState,
  AutoTradingConfig,
} from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    console.error("[API Error]", err.config?.url, err.message);
    return Promise.reject(err);
  }
);

// ─── System ──────────────────────────────────────────────────────────────────

export const systemApi = {
  health: () => api.get<{ status: string }>("/health"),
  status: () => api.get<SystemStatus>("/api/status"),
};

// ─── MT5 ─────────────────────────────────────────────────────────────────────

export const mt5Api = {
  status: () => api.get<MT5Status>("/api/mt5/status"),
  account: () => api.get<AccountInfo>("/api/mt5/account"),
  positions: () => api.get<MT5Position[]>("/api/mt5/positions"),
  history: (limit = 50) => api.get<MT5Position[]>(`/api/mt5/history?limit=${limit}`),
  connect: () => api.post<MT5Status>("/api/mt5/connect"),
  disconnect: () => api.post("/api/mt5/disconnect"),
  closePosition: (ticket: number) => api.post(`/api/mt5/positions/${ticket}/close`),
  closeAll: () => api.post("/api/mt5/positions/close-all"),
  placeOrder: (data: {
    symbol: string;
    direction: string;
    volume: number;
    sl: number;
    tp: number;
    comment?: string;
  }) => api.post<{ success: boolean; ticket: number; price: number }>("/api/mt5/orders", data),
};

// ─── Market ───────────────────────────────────────────────────────────────────

export const marketApi = {
  analysis: (symbol: string, timeframe = "H1") =>
    api.get<MarketAnalysis>(`/api/analysis/symbol/${symbol}?timeframe=${timeframe}`),
  watchlist: () => api.get("/api/market/overview"),
  price: (symbol: string) => api.get(`/api/market/price/${symbol}`),
};

// ─── Journal ──────────────────────────────────────────────────────────────────

export const journalApi = {
  list: (params?: { status?: string; limit?: number }) =>
    api.get<Trade[]>("/api/journal/trades", { params }),
  get: (id: number) => api.get<Trade>(`/api/journal/trades/${id}`),
  create: (data: Partial<Trade>) => api.post<Trade>("/api/journal/trades", data),
  update: (id: number, data: Partial<Trade>) =>
    api.patch<Trade>(`/api/journal/trades/${id}`, data),
  delete: (id: number) => api.delete(`/api/journal/trades/${id}`),
  analytics: () => api.get("/api/journal/analytics"),
  performance: () => api.get("/api/journal/performance"),
};

// ─── Signals ──────────────────────────────────────────────────────────────────

export const signalApi = {
  list: () => api.get<AISignal[]>("/api/signals"),
  approve: (id: string) => api.post(`/api/signals/${id}/approve`),
  reject: (id: string) => api.post(`/api/signals/${id}/reject`),
};

// ─── Risk ─────────────────────────────────────────────────────────────────────

export const riskApi = {
  state: () => api.get<RiskState>("/api/autonomous/risk"),
  reset: () => api.post("/api/autonomous/risk/reset"),
  config: () => api.get<AutoTradingConfig>("/api/autonomous/config"),
  updateConfig: (config: Partial<AutoTradingConfig>) =>
    api.patch<AutoTradingConfig>("/api/autonomous/config", config),
};

// ─── Autonomous Engine ────────────────────────────────────────────────────────

export const autonomousApi = {
  status:           () => api.get("/api/autonomous/status"),
  setMode:          (mode: string) => api.post("/api/autonomous/mode", { mode }),
  scan:             () => api.post("/api/autonomous/scan"),
  pending:          () => api.get("/api/autonomous/pending"),
  approve:          (id: string) => api.post(`/api/autonomous/pending/${id}/approve`),
  reject:           (id: string) => api.post(`/api/autonomous/pending/${id}/reject`),
  paperSummary:     () => api.get("/api/autonomous/paper/summary"),
  paperPositions:   () => api.get("/api/autonomous/paper/positions"),
  paperHistory:     (limit = 50) => api.get(`/api/autonomous/paper/history?limit=${limit}`),
  paperClose:       (id: string, exit_price?: number) =>
    api.post(`/api/autonomous/paper/positions/${id}/close`, exit_price ? { exit_price } : {}),
  paperReset:       () => api.post("/api/autonomous/paper/reset"),
};
