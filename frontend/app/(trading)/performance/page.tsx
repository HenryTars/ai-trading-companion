"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { EquityCurve } from "@/components/chart/EquityCurve";
import { journalApi } from "@/services/api";
import { cn, getPnlClass } from "@/lib/utils";
import {
  Activity, TrendingUp, TrendingDown, Target,
  BarChart2, Flame, Zap, Shield,
} from "lucide-react";

// ─── Types ────────────────────────────────────────────────────────────────────

interface Summary {
  total_trades:  number;
  closed_trades: number;
  open_trades:   number;
  wins:          number;
  losses:        number;
  breakeven:     number;
  win_rate:      number;
  avg_rr:        number;
  total_pnl_pct: number;
  profit_factor: number;
  max_drawdown:  number;
  best_trade:    number;
  worst_trade:   number;
  avg_win_pct:   number;
  avg_loss_pct:  number;
  streak:        { type: string; count: number } | null;
}

interface BreakdownRow {
  symbol?:   string;
  session?:  string;
  strategy?: string;
  trades:    number;
  wins:      number;
  losses:    number;
  win_rate:  number;
  pnl_pct:   number;
  avg_rr:    number;
}

interface Analytics {
  summary:      Summary;
  equity_curve: { time: string; value: number }[];
  by_symbol:    BreakdownRow[];
  by_session:   BreakdownRow[];
  by_strategy:  BreakdownRow[];
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function pct(n: number) {
  return `${n >= 0 ? "+" : ""}${n.toFixed(2)}%`;
}

// ─── Metric Card ─────────────────────────────────────────────────────────────

function MetricCard({
  label, value, sub, icon: Icon, valueClass, highlight,
}: {
  label: string;
  value: string;
  sub?: string;
  icon: React.ElementType;
  valueClass?: string;
  highlight?: boolean;
}) {
  return (
    <Card className={highlight ? "border-terminal-accent/40" : ""}>
      <CardContent className="p-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="text-[10px] uppercase tracking-wider text-terminal-muted mb-1">{label}</p>
            <p className={cn("text-xl font-mono font-bold truncate", valueClass ?? "text-terminal-text")}>
              {value}
            </p>
            {sub && <p className="text-xs text-terminal-muted mt-0.5">{sub}</p>}
          </div>
          <div className="w-8 h-8 rounded-md bg-terminal-secondary flex items-center justify-center shrink-0">
            <Icon className="w-4 h-4 text-terminal-muted" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Win/Loss Bar ─────────────────────────────────────────────────────────────

function WinLossBar({ wins, losses, breakeven }: { wins: number; losses: number; breakeven: number }) {
  const total = wins + losses + breakeven;
  if (total === 0) return null;
  const wp = (wins      / total) * 100;
  const lp = (losses    / total) * 100;
  const bp = (breakeven / total) * 100;

  return (
    <div className="space-y-2">
      <div className="flex rounded-full overflow-hidden h-3">
        <div className="bg-terminal-bull transition-all" style={{ width: `${wp}%` }} />
        <div className="bg-terminal-muted/40 transition-all" style={{ width: `${bp}%` }} />
        <div className="bg-terminal-bear transition-all" style={{ width: `${lp}%` }} />
      </div>
      <div className="flex items-center gap-4 text-xs text-terminal-muted">
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-terminal-bull inline-block" />
          {wins} wins ({wp.toFixed(0)}%)
        </span>
        {breakeven > 0 && (
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-terminal-muted/40 inline-block" />
            {breakeven} BE
          </span>
        )}
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-terminal-bear inline-block" />
          {losses} losses ({lp.toFixed(0)}%)
        </span>
      </div>
    </div>
  );
}

// ─── Breakdown Table ──────────────────────────────────────────────────────────

function BreakdownTable({
  title, rows, labelKey,
}: {
  title: string;
  rows:  BreakdownRow[];
  labelKey: "symbol" | "session" | "strategy";
}) {
  const maxTrades = Math.max(...rows.map((r) => r.trades), 1);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">{title}</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        {rows.length === 0 ? (
          <p className="text-sm text-terminal-muted text-center py-6">No data</p>
        ) : (
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-terminal-border text-terminal-muted">
                <th className="text-left px-3 py-2 font-medium">{title.split(" ")[1]}</th>
                <th className="text-right px-3 py-2 font-medium">Trades</th>
                <th className="text-right px-3 py-2 font-medium">Win %</th>
                <th className="text-right px-3 py-2 font-medium">P&L</th>
                <th className="text-right px-3 py-2 font-medium hidden sm:table-cell">R:R</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => {
                const label  = row[labelKey] ?? "—";
                const barPct = (row.trades / maxTrades) * 100;
                return (
                  <tr key={i} className="border-b border-terminal-border/50 hover:bg-terminal-hover transition-colors">
                    <td className="px-3 py-2.5">
                      <div className="space-y-0.5">
                        <p className="font-semibold">{label}</p>
                        <div className="w-full bg-terminal-secondary rounded-full h-1">
                          <div
                            className={cn("h-1 rounded-full", row.win_rate >= 50 ? "bg-terminal-bull" : "bg-terminal-bear")}
                            style={{ width: `${barPct}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="px-3 py-2.5 text-right font-mono">{row.trades}</td>
                    <td className={cn("px-3 py-2.5 text-right font-mono", row.win_rate >= 50 ? "text-terminal-bull" : "text-terminal-bear")}>
                      {row.win_rate.toFixed(0)}%
                    </td>
                    <td className={cn("px-3 py-2.5 text-right font-mono font-semibold", getPnlClass(row.pnl_pct))}>
                      {pct(row.pnl_pct)}
                    </td>
                    <td className="px-3 py-2.5 text-right font-mono hidden sm:table-cell text-terminal-muted">
                      1:{row.avg_rr.toFixed(1)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </CardContent>
    </Card>
  );
}

// ─── Empty State ─────────────────────────────────────────────────────────────

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-96 text-terminal-muted space-y-4">
      <BarChart2 className="w-16 h-16 opacity-20" />
      <div className="text-center space-y-1">
        <p className="font-semibold text-terminal-text">No performance data yet</p>
        <p className="text-sm">Log and close trades in the Journal to see your analytics here.</p>
      </div>
    </div>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default function PerformancePage() {
  const { data, isLoading } = useQuery<Analytics>({
    queryKey:       ["analytics"],
    queryFn:        () => journalApi.analytics().then((r) => r.data),
    refetchInterval: 60_000,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64 text-terminal-muted text-sm">
        <Activity className="w-4 h-4 mr-2 animate-pulse" /> Loading analytics…
      </div>
    );
  }

  const s = data?.summary;
  if (!s || s.closed_trades === 0) {
    return <EmptyState />;
  }

  const curve    = data.equity_curve ?? [];
  const isProfit = s.total_pnl_pct >= 0;

  return (
    <div className="space-y-4 animate-slide-up">

      {/* ── Key Metrics ─────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <MetricCard
          label="Total P&L"
          value={pct(s.total_pnl_pct)}
          sub={`${s.closed_trades} closed trades`}
          icon={isProfit ? TrendingUp : TrendingDown}
          valueClass={getPnlClass(s.total_pnl_pct)}
          highlight
        />
        <MetricCard
          label="Win Rate"
          value={`${s.win_rate.toFixed(1)}%`}
          sub={`${s.wins}W · ${s.losses}L · ${s.breakeven}BE`}
          icon={Target}
          valueClass={s.win_rate >= 50 ? "text-terminal-bull" : "text-terminal-bear"}
        />
        <MetricCard
          label="Profit Factor"
          value={s.profit_factor.toFixed(2)}
          sub={s.profit_factor >= 1.5 ? "Strong edge" : s.profit_factor >= 1 ? "Positive edge" : "No edge yet"}
          icon={Zap}
          valueClass={s.profit_factor >= 1.5 ? "text-terminal-bull" : s.profit_factor >= 1 ? "text-terminal-warning" : "text-terminal-bear"}
        />
        <MetricCard
          label="Avg R:R"
          value={`1:${s.avg_rr.toFixed(2)}`}
          sub={`Best: +${s.best_trade.toFixed(2)}% · Worst: ${s.worst_trade.toFixed(2)}%`}
          icon={BarChart2}
          valueClass={s.avg_rr >= 2 ? "text-terminal-bull" : "text-terminal-warning"}
        />
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <MetricCard
          label="Max Drawdown"
          value={`${s.max_drawdown.toFixed(2)}%`}
          sub="Peak-to-trough"
          icon={Shield}
          valueClass={s.max_drawdown > -10 ? "text-terminal-warning" : "text-terminal-bear"}
        />
        <MetricCard
          label="Avg Win"
          value={`+${s.avg_win_pct.toFixed(2)}%`}
          sub={`Avg Loss: ${s.avg_loss_pct.toFixed(2)}%`}
          icon={TrendingUp}
          valueClass="text-terminal-bull"
        />
        <MetricCard
          label="Open Trades"
          value={s.open_trades.toString()}
          sub={`${s.total_trades} total logged`}
          icon={Activity}
        />
        <Card>
          <CardContent className="p-3">
            <p className="text-[10px] uppercase tracking-wider text-terminal-muted mb-1">Streak</p>
            {s.streak ? (
              <div className="flex items-center gap-2">
                <Flame className={cn("w-5 h-5", s.streak.type === "win" ? "text-terminal-bull" : "text-terminal-bear")} />
                <span className={cn("text-xl font-mono font-bold", s.streak.type === "win" ? "text-terminal-bull" : "text-terminal-bear")}>
                  {s.streak.count}
                </span>
                <Badge variant={s.streak.type === "win" ? "bull" : "bear"} className="text-[10px]">
                  {s.streak.type}
                </Badge>
              </div>
            ) : (
              <p className="text-xl font-mono font-bold text-terminal-muted">—</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* ── Equity Curve ────────────────────────────────────────────────────── */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-terminal-accent" />
              Equity Curve
            </CardTitle>
            <span className={cn("text-sm font-mono font-semibold", getPnlClass(s.total_pnl_pct))}>
              {pct(s.total_pnl_pct)}
            </span>
          </div>
          <WinLossBar wins={s.wins} losses={s.losses} breakeven={s.breakeven} />
        </CardHeader>
        <CardContent className="pt-0">
          <EquityCurve data={curve} height={220} />
        </CardContent>
      </Card>

      {/* ── Breakdown Tables ─────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <BreakdownTable
          title="By Symbol"
          rows={data.by_symbol}
          labelKey="symbol"
        />
        <BreakdownTable
          title="By Session"
          rows={data.by_session}
          labelKey="session"
        />
        <BreakdownTable
          title="By Strategy"
          rows={data.by_strategy}
          labelKey="strategy"
        />
      </div>

    </div>
  );
}
