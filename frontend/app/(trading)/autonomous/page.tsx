"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { autonomousApi, riskApi } from "@/services/api";
import { cn, getPnlClass } from "@/lib/utils";
import {
  Bot, Zap, Shield, TrendingUp, TrendingDown, RefreshCw,
  CheckCircle, XCircle, AlertTriangle, Play, RotateCcw,
  Activity, Lock, Unlock, ChevronRight,
} from "lucide-react";

// ─── All tradeable symbols ────────────────────────────────────────────────────

const ALL_SYMBOLS = [
  { id: "XAUUSD",  label: "Gold",    group: "metals"  },
  { id: "EURUSD",  label: "EUR/USD", group: "forex"   },
  { id: "GBPUSD",  label: "GBP/USD", group: "forex"   },
  { id: "BTCUSDT", label: "Bitcoin", group: "crypto"  },
  { id: "ETHUSDT", label: "Ethereum",group: "crypto"  },
  { id: "US100",   label: "NAS100",  group: "indices" },
];

// Crypto trades 24/7; forex/metals are closed Sat–Sun
function isMarketOpen(group: string): boolean {
  const day = new Date().getDay(); // 0=Sun, 6=Sat
  if (group === "crypto") return true;
  return day !== 0 && day !== 6;
}

// ─── Types ────────────────────────────────────────────────────────────────────

type EngineMode = "manual" | "assisted" | "auto";

interface PaperSummary {
  balance: number; equity: number; starting_balance: number;
  total_return_pct: number; daily_pnl: number; daily_pnl_pct: number;
  open_positions: number; total_trades: number;
  wins: number; losses: number; win_rate: number; total_pnl_amount: number;
  consecutive_losses: number;
}

interface PendingSignal {
  id: string; symbol: string; timeframe: string;
  direction: "long" | "short"; bias: string;
  confidence: number; entry: number; sl: number; tp: number; rr: number;
  trend_strength: string; risk_level: string; narrative: string;
  created_at: string; status: string;
}

interface PaperPosition {
  id: string; symbol: string; direction: string;
  entry: number; sl: number; tp: number;
  risk_pct: number; risk_amount: number;
  strategy: string; notes: string; opened_at: string;
}

interface PaperTrade extends PaperPosition {
  exit: number; pnl_pct: number; pnl_amount: number;
  status: "win" | "loss" | "breakeven"; reason: string; closed_at: string;
}

interface RiskState {
  daily_pnl: number; daily_trades: number; open_trades: number;
  consecutive_losses: number; is_locked: boolean; lock_reason?: string;
  daily_drawdown_pct: number; available_risk: number;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function pct(n: number, decimals = 2) {
  return `${n >= 0 ? "+" : ""}${n.toFixed(decimals)}%`;
}

function fmtCurrency(n: number) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 2 }).format(n);
}

// ─── Mode Switcher ────────────────────────────────────────────────────────────

function ModeSwitcher({ mode, onChange, isLocked }: {
  mode: EngineMode;
  onChange: (m: EngineMode) => void;
  isLocked: boolean;
}) {
  const modes: { key: EngineMode; label: string; desc: string; icon: React.ElementType }[] = [
    { key: "manual",   label: "Manual",   desc: "Trade from chart page. No auto-scanning.", icon: Activity },
    { key: "assisted", label: "Assisted", desc: "AI scans and suggests. You approve each trade.", icon: Bot },
    { key: "auto",     label: "Auto",     desc: "AI scans and executes on paper account.", icon: Zap },
  ];

  return (
    <Card className={isLocked ? "border-terminal-bear/50" : "border-terminal-accent/30"}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Bot className="w-4 h-4 text-terminal-accent" />
            Engine Mode
          </CardTitle>
          {isLocked ? (
            <Badge variant="bear" className="flex items-center gap-1">
              <Lock className="w-2.5 h-2.5" /> Locked
            </Badge>
          ) : (
            <Badge variant="bull" className="flex items-center gap-1">
              <Unlock className="w-2.5 h-2.5" /> Active
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-2">
          {modes.map(({ key, label, desc, icon: Icon }) => (
            <button
              key={key}
              onClick={() => onChange(key)}
              className={cn(
                "p-3 rounded-lg border text-left transition-all",
                mode === key
                  ? key === "auto"
                    ? "bg-terminal-bull/10 border-terminal-bull text-terminal-bull"
                    : key === "assisted"
                    ? "bg-terminal-accent/10 border-terminal-accent text-terminal-accent"
                    : "bg-terminal-secondary border-terminal-muted text-terminal-text"
                  : "border-terminal-border text-terminal-muted hover:border-terminal-accent hover:text-terminal-text"
              )}
            >
              <div className="flex items-center gap-1.5 mb-1">
                <Icon className="w-3.5 h-3.5" />
                <span className="text-sm font-semibold">{label}</span>
                {mode === key && <ChevronRight className="w-3 h-3 ml-auto" />}
              </div>
              <p className="text-[10px] opacity-70 leading-tight">{desc}</p>
            </button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Paper Account Cards ──────────────────────────────────────────────────────

function PaperAccountPanel({ summary }: { summary: PaperSummary }) {
  const stats = [
    {
      label: "Balance",
      value: fmtCurrency(summary.balance),
      sub: `Started ${fmtCurrency(summary.starting_balance)}`,
      icon: TrendingUp,
      vClass: summary.total_return_pct >= 0 ? "text-terminal-bull" : "text-terminal-bear",
    },
    {
      label: "Total Return",
      value: pct(summary.total_return_pct),
      sub: `${fmtCurrency(summary.total_pnl_amount)} net`,
      icon: TrendingUp,
      vClass: getPnlClass(summary.total_return_pct),
    },
    {
      label: "Daily P&L",
      value: pct(summary.daily_pnl_pct),
      sub: fmtCurrency(summary.daily_pnl),
      icon: Activity,
      vClass: getPnlClass(summary.daily_pnl_pct),
    },
    {
      label: "Win Rate",
      value: `${summary.win_rate.toFixed(1)}%`,
      sub: `${summary.wins}W · ${summary.losses}L · ${summary.total_trades} trades`,
      icon: Shield,
      vClass: summary.win_rate >= 50 ? "text-terminal-bull" : "text-terminal-bear",
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {stats.map(({ label, value, sub, icon: Icon, vClass }) => (
        <Card key={label}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <p className="text-[10px] uppercase tracking-wider text-terminal-muted mb-1">{label}</p>
                <p className={cn("text-xl font-mono font-bold truncate", vClass)}>{value}</p>
                <p className="text-xs text-terminal-muted mt-0.5">{sub}</p>
              </div>
              <div className="w-7 h-7 rounded-md bg-terminal-secondary flex items-center justify-center shrink-0">
                <Icon className="w-3.5 h-3.5 text-terminal-muted" />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// ─── Risk State Panel ─────────────────────────────────────────────────────────

function RiskPanel({ risk, config }: { risk: RiskState; config: Record<string, unknown> }) {
  const rules = [
    {
      label: "Daily Drawdown",
      value: `${risk.daily_drawdown_pct.toFixed(2)}%`,
      limit: `Limit: -${config.max_daily_drawdown ?? 3}%`,
      ok: risk.daily_drawdown_pct > -(config.max_daily_drawdown as number ?? 3),
    },
    {
      label: "Consecutive Losses",
      value: `${risk.consecutive_losses}`,
      limit: "Limit: 3",
      ok: risk.consecutive_losses < 3,
    },
    {
      label: "Open Positions",
      value: `${risk.open_trades}`,
      limit: `Max: ${config.max_open_trades ?? 3}`,
      ok: risk.open_trades < (config.max_open_trades as number ?? 3),
    },
    {
      label: "Daily Trades",
      value: `${risk.daily_trades}`,
      limit: `Max: ${config.max_daily_trades ?? 5}`,
      ok: risk.daily_trades < (config.max_daily_trades as number ?? 5),
    },
  ];

  return (
    <Card className={risk.is_locked ? "border-terminal-bear/50" : ""}>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm">
          <Shield className="w-3.5 h-3.5 text-terminal-accent" />
          Risk Monitor
          {risk.is_locked && (
            <Badge variant="bear" className="ml-auto text-[10px] flex items-center gap-1">
              <Lock className="w-2.5 h-2.5" /> {risk.lock_reason}
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {rules.map(({ label, value, limit, ok }) => (
          <div key={label} className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {ok
                ? <CheckCircle className="w-3 h-3 text-terminal-bull" />
                : <XCircle    className="w-3 h-3 text-terminal-bear" />}
              <span className="text-xs text-terminal-muted">{label}</span>
            </div>
            <div className="text-right">
              <span className={cn("text-xs font-mono font-semibold", ok ? "text-terminal-text" : "text-terminal-bear")}>
                {value}
              </span>
              <span className="text-[10px] text-terminal-muted ml-2">{limit}</span>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

// ─── Signal Queue ─────────────────────────────────────────────────────────────

function SignalQueue({
  signals, mode, isLocked, isScanning, onScan, onApprove, onReject,
}: {
  signals: PendingSignal[];
  mode: EngineMode;
  isLocked: boolean;
  isScanning: boolean;
  onScan: (symbols: string[]) => void;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
}) {
  const [selected, setSelected] = useState<Set<string>>(
    () => new Set(ALL_SYMBOLS.filter(s => isMarketOpen(s.group)).map(s => s.id))
  );

  function toggleSymbol(id: string) {
    setSelected(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  const openSymbols   = ALL_SYMBOLS.filter(s => isMarketOpen(s.group));
  const closedSymbols = ALL_SYMBOLS.filter(s => !isMarketOpen(s.group));

  return (
    <Card className="flex flex-col">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-sm">
            <Zap className="w-3.5 h-3.5 text-terminal-accent" />
            Signal Queue
            {signals.length > 0 && (
              <Badge variant="warning" className="text-[10px]">{signals.length} pending</Badge>
            )}
          </CardTitle>
          {mode !== "manual" && (
            <Button
              variant="outline"
              onClick={() => onScan(Array.from(selected))}
              disabled={isScanning || isLocked || selected.size === 0}
              className="gap-1.5 h-7 text-xs"
            >
              {isScanning
                ? <RefreshCw className="w-3 h-3 animate-spin" />
                : <Play className="w-3 h-3" />}
              {isScanning ? "Scanning…" : `Scan (${selected.size})`}
            </Button>
          )}
        </div>

        {/* Symbol selector chips */}
        {mode !== "manual" && (
          <div className="space-y-1.5 pt-1">
            <div className="flex flex-wrap gap-1">
              {openSymbols.map(({ id, label }) => (
                <button
                  key={id}
                  onClick={() => toggleSymbol(id)}
                  className={cn(
                    "px-2 py-0.5 rounded-full text-[10px] font-medium border transition-all",
                    selected.has(id)
                      ? "bg-terminal-accent/20 border-terminal-accent text-terminal-accent"
                      : "bg-transparent border-terminal-border text-terminal-muted hover:border-terminal-accent/50"
                  )}
                >
                  {label}
                </button>
              ))}
            </div>
            {closedSymbols.length > 0 && (
              <div className="flex flex-wrap gap-1 items-center">
                <span className="text-[10px] text-terminal-muted">Closed:</span>
                {closedSymbols.map(({ id, label }) => (
                  <span key={id} className="px-2 py-0.5 rounded-full text-[10px] border border-terminal-border/40 text-terminal-muted/40 line-through">
                    {label}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </CardHeader>
      <CardContent className="flex-1 space-y-2 overflow-auto max-h-80">
        {mode === "manual" ? (
          <p className="text-sm text-terminal-muted text-center py-8">
            Switch to Assisted or Auto mode to enable scanning.
          </p>
        ) : isLocked ? (
          <div className="flex flex-col items-center justify-center py-8 gap-2 text-terminal-bear">
            <Lock className="w-8 h-8 opacity-40" />
            <p className="text-sm">Risk limits active — scanning paused</p>
          </div>
        ) : signals.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-terminal-muted">
            <Bot className="w-8 h-8 mb-2 opacity-20" />
            <p className="text-sm">No signals yet.</p>
            <p className="text-xs mt-1">Press Scan Markets to analyse the watchlist.</p>
          </div>
        ) : (
          signals.map((sig) => (
            <div
              key={sig.id}
              className="border border-terminal-border rounded-lg p-3 space-y-2 hover:bg-terminal-hover transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-sm">{sig.symbol}</span>
                  <Badge variant={sig.direction === "long" ? "bull" : "bear"} className="text-[10px]">
                    {sig.direction.toUpperCase()}
                  </Badge>
                  <Badge variant="muted" className="text-[10px]">{sig.timeframe}</Badge>
                </div>
                <div className="flex items-center gap-1">
                  <span className={cn(
                    "text-xs font-mono font-bold",
                    sig.confidence >= 0.80 ? "text-terminal-bull" :
                    sig.confidence >= 0.65 ? "text-terminal-warning" : "text-terminal-muted"
                  )}>
                    {Math.round(sig.confidence * 100)}%
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2 text-[10px] text-terminal-muted">
                <div>
                  <p className="uppercase tracking-wide">Entry</p>
                  <p className="font-mono text-terminal-text">{sig.entry.toFixed(5)}</p>
                </div>
                <div>
                  <p className="uppercase tracking-wide">SL</p>
                  <p className="font-mono text-terminal-bear">{sig.sl.toFixed(5)}</p>
                </div>
                <div>
                  <p className="uppercase tracking-wide">TP / R:R</p>
                  <p className="font-mono text-terminal-bull">{sig.tp.toFixed(5)} · 1:{sig.rr.toFixed(1)}</p>
                </div>
              </div>

              {mode === "assisted" && (
                <div className="flex gap-2 pt-1">
                  <Button
                    variant="bull"
                    className="flex-1 h-7 text-xs gap-1"
                    onClick={() => onApprove(sig.id)}
                  >
                    <CheckCircle className="w-3 h-3" /> Execute
                  </Button>
                  <Button
                    variant="bear"
                    className="flex-1 h-7 text-xs gap-1"
                    onClick={() => onReject(sig.id)}
                  >
                    <XCircle className="w-3 h-3" /> Reject
                  </Button>
                </div>
              )}
              {mode === "auto" && (
                <p className="text-[10px] text-terminal-muted flex items-center gap-1">
                  <Zap className="w-2.5 h-2.5" /> Auto-executed on approval
                </p>
              )}
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}

// ─── Paper Positions ──────────────────────────────────────────────────────────

function PaperPositions({ positions, onClose }: {
  positions: PaperPosition[];
  onClose: (id: string) => void;
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            <Activity className="w-3.5 h-3.5 text-terminal-accent" />
            Paper Positions
          </CardTitle>
          <Badge variant={positions.length > 0 ? "warning" : "muted"} className="text-[10px]">
            {positions.length} open
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        {positions.length === 0 ? (
          <p className="text-sm text-terminal-muted text-center py-6">No open paper positions</p>
        ) : (
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-terminal-border text-terminal-muted">
                <th className="text-left px-3 py-2 font-medium">Symbol</th>
                <th className="text-left px-3 py-2 font-medium">Dir</th>
                <th className="text-right px-3 py-2 font-medium">Entry</th>
                <th className="text-right px-3 py-2 font-medium">SL</th>
                <th className="text-right px-3 py-2 font-medium">TP</th>
                <th className="text-right px-3 py-2 font-medium">Risk $</th>
                <th className="px-3 py-2" />
              </tr>
            </thead>
            <tbody>
              {positions.map((pos) => (
                <tr key={pos.id} className="border-b border-terminal-border/50 hover:bg-terminal-hover group">
                  <td className="px-3 py-2.5 font-semibold">{pos.symbol}</td>
                  <td className="px-3 py-2.5">
                    <Badge variant={pos.direction === "long" ? "bull" : "bear"} className="text-[10px]">
                      {pos.direction.toUpperCase()}
                    </Badge>
                  </td>
                  <td className="px-3 py-2.5 text-right font-mono">{pos.entry.toFixed(5)}</td>
                  <td className="px-3 py-2.5 text-right font-mono text-terminal-bear">{pos.sl.toFixed(5)}</td>
                  <td className="px-3 py-2.5 text-right font-mono text-terminal-bull">{pos.tp.toFixed(5)}</td>
                  <td className="px-3 py-2.5 text-right font-mono">{fmtCurrency(pos.risk_amount)}</td>
                  <td className="px-3 py-2.5">
                    <Button
                      size="icon"
                      variant="ghost"
                      className="w-6 h-6 opacity-0 group-hover:opacity-100 hover:text-terminal-bear hover:bg-terminal-bear/10"
                      onClick={() => onClose(pos.id)}
                    >
                      <XCircle className="w-3 h-3" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </CardContent>
    </Card>
  );
}

// ─── Paper History ────────────────────────────────────────────────────────────

function PaperHistory({ trades }: { trades: PaperTrade[] }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Paper Trade History</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        {trades.length === 0 ? (
          <p className="text-sm text-terminal-muted text-center py-6">No closed paper trades yet</p>
        ) : (
          <div className="overflow-x-auto max-h-64 overflow-y-auto">
            <table className="w-full text-xs">
              <thead className="sticky top-0 bg-terminal-card">
                <tr className="border-b border-terminal-border text-terminal-muted">
                  <th className="text-left px-3 py-2 font-medium">Symbol</th>
                  <th className="text-left px-3 py-2 font-medium">Dir</th>
                  <th className="text-right px-3 py-2 font-medium">Entry</th>
                  <th className="text-right px-3 py-2 font-medium">Exit</th>
                  <th className="text-right px-3 py-2 font-medium">P&L %</th>
                  <th className="text-right px-3 py-2 font-medium">P&L $</th>
                  <th className="text-left px-3 py-2 font-medium">Outcome</th>
                  <th className="text-left px-3 py-2 font-medium hidden md:table-cell">Closed</th>
                </tr>
              </thead>
              <tbody>
                {trades.map((t) => (
                  <tr key={t.id} className="border-b border-terminal-border/50 hover:bg-terminal-hover">
                    <td className="px-3 py-2 font-semibold">{t.symbol}</td>
                    <td className="px-3 py-2">
                      <Badge variant={t.direction === "long" ? "bull" : "bear"} className="text-[10px]">
                        {t.direction.toUpperCase()}
                      </Badge>
                    </td>
                    <td className="px-3 py-2 text-right font-mono">{t.entry.toFixed(5)}</td>
                    <td className="px-3 py-2 text-right font-mono">{t.exit.toFixed(5)}</td>
                    <td className={cn("px-3 py-2 text-right font-mono font-semibold", getPnlClass(t.pnl_pct))}>
                      {pct(t.pnl_pct, 3)}
                    </td>
                    <td className={cn("px-3 py-2 text-right font-mono", getPnlClass(t.pnl_amount))}>
                      {fmtCurrency(t.pnl_amount)}
                    </td>
                    <td className="px-3 py-2">
                      <Badge
                        variant={t.status === "win" ? "bull" : t.status === "loss" ? "bear" : "muted"}
                        className="text-[10px] uppercase"
                      >
                        {t.status}
                      </Badge>
                    </td>
                    <td className="px-3 py-2 text-terminal-muted hidden md:table-cell whitespace-nowrap">
                      {new Date(t.closed_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default function AutonomousPage() {
  const [isScanning, setIsScanning] = useState(false);
  const qc = useQueryClient();

  const { data: status }    = useQuery({ queryKey: ["auto-status"],    queryFn: () => autonomousApi.status().then((r) => r.data),    refetchInterval: 5_000 });
  const { data: config }    = useQuery({ queryKey: ["auto-config"],    queryFn: () => riskApi.config().then((r) => r.data),           refetchInterval: 30_000 });
  const { data: risk }      = useQuery({ queryKey: ["auto-risk"],      queryFn: () => riskApi.state().then((r) => r.data),            refetchInterval: 5_000 });
  const { data: pending = [] } = useQuery({ queryKey: ["auto-pending"], queryFn: () => autonomousApi.pending().then((r) => r.data),   refetchInterval: 5_000 });
  const { data: positions = [] } = useQuery({ queryKey: ["paper-pos"],  queryFn: () => autonomousApi.paperPositions().then((r) => r.data), refetchInterval: 5_000 });
  const { data: history = [] }   = useQuery({ queryKey: ["paper-hist"], queryFn: () => autonomousApi.paperHistory().then((r) => r.data),  refetchInterval: 15_000 });
  const { data: paperSummary }   = useQuery({ queryKey: ["paper-sum"],  queryFn: () => autonomousApi.paperSummary().then((r) => r.data),   refetchInterval: 5_000 });

  const mode:      EngineMode = (status?.mode ?? "assisted") as EngineMode;
  const isLocked:  boolean    = status?.is_locked ?? false;

  const modeMutation = useMutation({
    mutationFn: (m: EngineMode) => autonomousApi.setMode(m),
    onSuccess:  () => qc.invalidateQueries({ queryKey: ["auto-status"] }),
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) => autonomousApi.approve(id),
    onSuccess: (res) => {
      const data = res.data as { ok: boolean; ticket?: number; price?: number; error?: string };
      if (data.ok && data.ticket) {
        alert(`✅ MT5 order placed! Ticket #${data.ticket} @ ${data.price?.toFixed(5)}`);
      } else if (!data.ok) {
        alert(`❌ Order failed: ${data.error}`);
      }
      qc.invalidateQueries({ queryKey: ["auto-pending"] });
      qc.invalidateQueries({ queryKey: ["paper-pos"] });
      qc.invalidateQueries({ queryKey: ["paper-sum"] });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: (id: string) => autonomousApi.reject(id),
    onSuccess:  () => qc.invalidateQueries({ queryKey: ["auto-pending"] }),
  });

  const closeMutation = useMutation({
    mutationFn: (id: string) => autonomousApi.paperClose(id),
    onSuccess:  () => { qc.invalidateQueries({ queryKey: ["paper-pos"] }); qc.invalidateQueries({ queryKey: ["paper-hist"] }); qc.invalidateQueries({ queryKey: ["paper-sum"] }); },
  });

  const resetMutation = useMutation({
    mutationFn: () => autonomousApi.paperReset(),
    onSuccess:  () => { qc.invalidateQueries({ queryKey: ["paper-sum"] }); qc.invalidateQueries({ queryKey: ["paper-pos"] }); qc.invalidateQueries({ queryKey: ["paper-hist"] }); qc.invalidateQueries({ queryKey: ["auto-status"] }); },
  });

  async function handleScan(symbols: string[]) {
    setIsScanning(true);
    try {
      await autonomousApi.scan(symbols);
      qc.invalidateQueries({ queryKey: ["auto-pending"] });
      qc.invalidateQueries({ queryKey: ["auto-status"] });
    } finally {
      setIsScanning(false);
    }
  }

  const defaultPaper: PaperSummary = {
    balance: 10000, equity: 10000, starting_balance: 10000,
    total_return_pct: 0, daily_pnl: 0, daily_pnl_pct: 0,
    open_positions: 0, total_trades: 0, wins: 0, losses: 0,
    win_rate: 0, total_pnl_amount: 0, consecutive_losses: 0,
  };

  const defaultRisk: RiskState = {
    daily_pnl: 0, daily_trades: 0, open_trades: 0,
    consecutive_losses: 0, is_locked: false,
    daily_drawdown_pct: 0, available_risk: 1,
  };

  return (
    <div className="space-y-4 animate-slide-up">

      {/* Mode switcher */}
      <ModeSwitcher
        mode={mode}
        onChange={(m) => modeMutation.mutate(m)}
        isLocked={isLocked}
      />

      {/* Paper account */}
      <PaperAccountPanel summary={paperSummary ?? defaultPaper} />

      {/* Scanner + Risk side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <SignalQueue
            signals={pending as PendingSignal[]}
            mode={mode}
            isLocked={isLocked}
            isScanning={isScanning}
            onScan={(syms) => handleScan(syms)}
            onApprove={(id) => approveMutation.mutate(id)}
            onReject={(id) => rejectMutation.mutate(id)}
          />
        </div>
        <div className="space-y-3">
          <RiskPanel risk={risk ?? defaultRisk} config={config ?? {}} />
          {/* Lot size + controls */}
          <Card>
            <CardContent className="p-3 space-y-2">
              <div className="flex items-center justify-between gap-2">
                <span className="text-[10px] text-terminal-muted uppercase tracking-wide">Lot Size</span>
                <input
                  type="number"
                  min="0.01" max="10" step="0.01"
                  defaultValue={config?.volume ?? 0.01}
                  onBlur={(e) => {
                    const v = parseFloat(e.target.value);
                    if (v > 0) riskApi.updateConfig({ volume: v });
                  }}
                  className="w-20 text-right font-mono text-xs bg-terminal-secondary border border-terminal-border rounded px-2 py-1 text-terminal-text focus:outline-none focus:border-terminal-accent"
                />
              </div>
              <p className="text-[10px] text-terminal-muted">
                Lot size applied to all MT5 orders (0.01 = micro lot)
              </p>
              {status?.last_scan && (
                <p className="text-[10px] text-terminal-muted flex items-center gap-1 pt-1">
                  <RefreshCw className="w-2.5 h-2.5" />
                  Last scan: {new Date(status.last_scan).toLocaleTimeString()}
                </p>
              )}
              <Button
                variant="destructive"
                className="w-full h-7 text-xs gap-1.5"
                onClick={() => {
                  if (confirm("Reset paper account to $10,000? This cannot be undone.")) {
                    resetMutation.mutate();
                  }
                }}
              >
                <RotateCcw className="w-3 h-3" />
                Reset Paper Account
              </Button>
              {isLocked && (
                <div className="flex items-start gap-2 text-[10px] text-terminal-bear bg-terminal-bear/10 rounded-md p-2">
                  <AlertTriangle className="w-3 h-3 shrink-0 mt-0.5" />
                  <p>{status?.lock_reason}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Paper positions + history */}
      <PaperPositions
        positions={positions as PaperPosition[]}
        onClose={(id) => closeMutation.mutate(id)}
      />
      <PaperHistory trades={history as PaperTrade[]} />

    </div>
  );
}
