import { create } from "zustand";
import { subscribeWithSelector } from "zustand/middleware";
import type {
  MT5Status,
  AccountInfo,
  MT5Position,
  AISignal,
  PriceTick,
  RiskState,
  TradingMode,
  SystemStatus,
} from "@/types";

// ─── Price store ──────────────────────────────────────────────────────────────

interface PriceStore {
  ticks: Record<string, PriceTick>;
  setTick: (tick: PriceTick) => void;
}

export const usePriceStore = create<PriceStore>((set) => ({
  ticks: {},
  setTick: (tick) =>
    set((s) => ({ ticks: { ...s.ticks, [tick.symbol]: tick } })),
}));

// ─── MT5 store ────────────────────────────────────────────────────────────────

interface MT5Store {
  status: MT5Status;
  account: AccountInfo | null;
  positions: MT5Position[];
  setStatus: (s: MT5Status) => void;
  setAccount: (a: AccountInfo) => void;
  setPositions: (p: MT5Position[]) => void;
  updatePosition: (p: MT5Position) => void;
  removePosition: (ticket: number) => void;
}

export const useMT5Store = create<MT5Store>()(
  subscribeWithSelector((set) => ({
    status: { connected: false },
    account: null,
    positions: [],
    setStatus: (status) => set({ status }),
    setAccount: (account) => set({ account }),
    setPositions: (positions) => set({ positions }),
    updatePosition: (pos) =>
      set((s) => ({
        positions: s.positions.some((p) => p.ticket === pos.ticket)
          ? s.positions.map((p) => (p.ticket === pos.ticket ? pos : p))
          : [...s.positions, pos],
      })),
    removePosition: (ticket) =>
      set((s) => ({ positions: s.positions.filter((p) => p.ticket !== ticket) })),
  }))
);

// ─── Signals store ────────────────────────────────────────────────────────────

interface SignalStore {
  signals: AISignal[];
  pendingCount: number;
  setSignals: (signals: AISignal[]) => void;
  addSignal: (signal: AISignal) => void;
}

export const useSignalStore = create<SignalStore>((set) => ({
  signals: [],
  pendingCount: 0,
  setSignals: (signals) => set({ signals, pendingCount: signals.length }),
  addSignal: (signal) =>
    set((s) => ({ signals: [signal, ...s.signals].slice(0, 50), pendingCount: s.pendingCount + 1 })),
}));

// ─── Risk store ───────────────────────────────────────────────────────────────

interface RiskStore {
  state: RiskState | null;
  setState: (s: RiskState) => void;
}

export const useRiskStore = create<RiskStore>((set) => ({
  state: null,
  setState: (state) => set({ state }),
}));

// ─── App/UI store ─────────────────────────────────────────────────────────────

interface AppStore {
  systemStatus: SystemStatus | null;
  tradingMode: TradingMode;
  sidebarCollapsed: boolean;
  activeSymbol: string;
  activeTimeframe: string;
  setSystemStatus: (s: SystemStatus) => void;
  setTradingMode: (m: TradingMode) => void;
  setSidebarCollapsed: (v: boolean) => void;
  setActiveSymbol: (s: string) => void;
  setActiveTimeframe: (tf: string) => void;
}

export const useAppStore = create<AppStore>((set) => ({
  systemStatus: null,
  tradingMode: "assisted",
  sidebarCollapsed: false,
  activeSymbol: "XAUUSD",
  activeTimeframe: "H1",
  setSystemStatus: (systemStatus) => set({ systemStatus }),
  setTradingMode: (tradingMode) => set({ tradingMode }),
  setSidebarCollapsed: (sidebarCollapsed) => set({ sidebarCollapsed }),
  setActiveSymbol: (activeSymbol) => set({ activeSymbol }),
  setActiveTimeframe: (activeTimeframe) => set({ activeTimeframe }),
}));
