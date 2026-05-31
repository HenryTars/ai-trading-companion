"use client";

import { useState, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { journalApi } from "@/services/api";
import { cn, formatPrice, getPnlClass } from "@/lib/utils";
import type { Trade } from "@/types";
import {
  BookOpen, Plus, X, TrendingUp, TrendingDown,
  Trash2, CheckCircle, ChevronDown, RefreshCw,
} from "lucide-react";

// ─── Types ────────────────────────────────────────────────────────────────────

type FilterStatus = "all" | "open" | "win" | "loss" | "breakeven";

// ─── Helpers ─────────────────────────────────────────────────────────────────

const SYMBOLS    = ["XAUUSD", "EURUSD", "GBPUSD", "BTCUSDT", "US100"];
const SESSIONS   = ["London", "New York", "Asian", "Sydney", "Overlap"];
const STRATEGIES = ["SMC", "ICT", "Price Action", "Scalp", "Swing", "Breakout", "Other"];

function statusBadge(status: string) {
  const variants: Record<string, "bull" | "bear" | "warning" | "muted" | "default"> = {
    win:        "bull",
    loss:       "bear",
    open:       "warning",
    breakeven:  "muted",
  };
  return <Badge variant={variants[status] ?? "default"} className="text-[10px] uppercase">{status}</Badge>;
}

function dirBadge(dir: string) {
  return (
    <Badge variant={dir === "long" ? "bull" : "bear"} className="text-[10px] uppercase flex items-center gap-0.5">
      {dir === "long" ? <TrendingUp className="w-2.5 h-2.5" /> : <TrendingDown className="w-2.5 h-2.5" />}
      {dir}
    </Badge>
  );
}

// ─── Add Trade Modal ──────────────────────────────────────────────────────────

interface AddTradeForm {
  symbol: string;
  direction: "long" | "short";
  entry_price: string;
  stop_loss: string;
  take_profit: string;
  risk_percent: string;
  session: string;
  strategy: string;
  notes: string;
}

const DEFAULT_FORM: AddTradeForm = {
  symbol:       "XAUUSD",
  direction:    "long",
  entry_price:  "",
  stop_loss:    "",
  take_profit:  "",
  risk_percent: "1",
  session:      "",
  strategy:     "",
  notes:        "",
};

function AddTradeModal({ onClose }: { onClose: () => void }) {
  const [form, setForm] = useState<AddTradeForm>(DEFAULT_FORM);
  const qc = useQueryClient();

  const mutation = useMutation({
    mutationFn: () =>
      journalApi.create({
        symbol:       form.symbol,
        direction:    form.direction,
        entry_price:  parseFloat(form.entry_price),
        stop_loss:    parseFloat(form.stop_loss),
        take_profit:  parseFloat(form.take_profit),
        risk_percent: parseFloat(form.risk_percent) || 1,
        session:      form.session || undefined,
        strategy:     form.strategy || undefined,
        notes:        form.notes || undefined,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["trades"] });
      onClose();
    },
  });

  const entry  = parseFloat(form.entry_price) || 0;
  const sl     = parseFloat(form.stop_loss)   || 0;
  const tp     = parseFloat(form.take_profit) || 0;
  const risk   = entry > 0 && sl > 0 ? Math.abs(entry - sl) : 0;
  const reward = entry > 0 && tp > 0 ? Math.abs(tp - entry) : 0;
  const rr     = risk > 0 ? (reward / risk).toFixed(2) : "—";

  const set = (k: keyof AddTradeForm) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  const valid = form.entry_price && form.stop_loss && form.take_profit && !isNaN(parseFloat(form.entry_price));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div
        className="bg-terminal-card border border-terminal-border rounded-xl w-full max-w-lg mx-4 shadow-2xl animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-terminal-border">
          <h2 className="font-semibold text-terminal-text flex items-center gap-2">
            <Plus className="w-4 h-4 text-terminal-accent" /> Log New Trade
          </h2>
          <button onClick={onClose} className="text-terminal-muted hover:text-terminal-text transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="p-5 space-y-4 max-h-[70vh] overflow-y-auto">
          {/* Symbol + Direction */}
          <div className="grid grid-cols-2 gap-3">
            <label className="space-y-1">
              <span className="text-xs text-terminal-muted">Symbol</span>
              <select
                value={form.symbol}
                onChange={set("symbol")}
                className="w-full bg-terminal-secondary border border-terminal-border rounded-md px-3 py-2 text-sm text-terminal-text focus:outline-none focus:border-terminal-accent"
              >
                {SYMBOLS.map((s) => <option key={s}>{s}</option>)}
              </select>
            </label>
            <label className="space-y-1">
              <span className="text-xs text-terminal-muted">Direction</span>
              <div className="flex rounded-md overflow-hidden border border-terminal-border">
                {(["long", "short"] as const).map((d) => (
                  <button
                    key={d}
                    onClick={() => setForm((f) => ({ ...f, direction: d }))}
                    className={cn(
                      "flex-1 py-2 text-sm font-medium transition-colors uppercase",
                      form.direction === d
                        ? d === "long"
                          ? "bg-terminal-bull text-white"
                          : "bg-terminal-bear text-white"
                        : "bg-terminal-secondary text-terminal-muted hover:text-terminal-text"
                    )}
                  >
                    {d}
                  </button>
                ))}
              </div>
            </label>
          </div>

          {/* Prices */}
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: "Entry Price", key: "entry_price" as const },
              { label: "Stop Loss",   key: "stop_loss"   as const },
              { label: "Take Profit", key: "take_profit" as const },
            ].map(({ label, key }) => (
              <label key={key} className="space-y-1">
                <span className="text-xs text-terminal-muted">{label}</span>
                <input
                  type="number"
                  step="any"
                  placeholder="0.00"
                  value={form[key]}
                  onChange={set(key)}
                  className="w-full bg-terminal-secondary border border-terminal-border rounded-md px-3 py-2 text-sm text-terminal-text focus:outline-none focus:border-terminal-accent font-mono"
                />
              </label>
            ))}
          </div>

          {/* R:R preview */}
          {risk > 0 && (
            <div className="flex items-center gap-4 text-xs bg-terminal-bg px-3 py-2 rounded-md border border-terminal-border">
              <span className="text-terminal-muted">R:R</span>
              <span className={cn("font-mono font-semibold", parseFloat(rr) >= 2 ? "text-terminal-bull" : "text-terminal-warning")}>
                1:{rr}
              </span>
              <span className="text-terminal-muted">Risk {risk.toFixed(5)}</span>
              <span className="text-terminal-muted">Reward {reward.toFixed(5)}</span>
            </div>
          )}

          {/* Risk % + Session */}
          <div className="grid grid-cols-2 gap-3">
            <label className="space-y-1">
              <span className="text-xs text-terminal-muted">Risk %</span>
              <input
                type="number"
                step="0.1"
                min="0.1"
                max="10"
                value={form.risk_percent}
                onChange={set("risk_percent")}
                className="w-full bg-terminal-secondary border border-terminal-border rounded-md px-3 py-2 text-sm text-terminal-text focus:outline-none focus:border-terminal-accent font-mono"
              />
            </label>
            <label className="space-y-1">
              <span className="text-xs text-terminal-muted">Session</span>
              <select
                value={form.session}
                onChange={set("session")}
                className="w-full bg-terminal-secondary border border-terminal-border rounded-md px-3 py-2 text-sm text-terminal-text focus:outline-none focus:border-terminal-accent"
              >
                <option value="">— optional —</option>
                {SESSIONS.map((s) => <option key={s}>{s}</option>)}
              </select>
            </label>
          </div>

          {/* Strategy */}
          <label className="space-y-1">
            <span className="text-xs text-terminal-muted">Strategy</span>
            <select
              value={form.strategy}
              onChange={set("strategy")}
              className="w-full bg-terminal-secondary border border-terminal-border rounded-md px-3 py-2 text-sm text-terminal-text focus:outline-none focus:border-terminal-accent"
            >
              <option value="">— optional —</option>
              {STRATEGIES.map((s) => <option key={s}>{s}</option>)}
            </select>
          </label>

          {/* Notes */}
          <label className="space-y-1">
            <span className="text-xs text-terminal-muted">Notes</span>
            <textarea
              rows={3}
              placeholder="Trade rationale, confluences…"
              value={form.notes}
              onChange={set("notes")}
              className="w-full bg-terminal-secondary border border-terminal-border rounded-md px-3 py-2 text-sm text-terminal-text focus:outline-none focus:border-terminal-accent resize-none"
            />
          </label>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-5 py-4 border-t border-terminal-border">
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button
            variant="bull"
            disabled={!valid || mutation.isPending}
            onClick={() => mutation.mutate()}
          >
            {mutation.isPending ? "Saving…" : "Log Trade"}
          </Button>
        </div>
        {mutation.isError && (
          <p className="text-xs text-terminal-bear text-center pb-3">{String(mutation.error)}</p>
        )}
      </div>
    </div>
  );
}

// ─── Close Trade Modal ────────────────────────────────────────────────────────

function CloseTradeModal({ trade, onClose }: { trade: Trade; onClose: () => void }) {
  const [exitPrice, setExitPrice] = useState("");
  const [outcome, setOutcome]     = useState<"win" | "loss" | "breakeven">("win");
  const qc = useQueryClient();

  const entry = trade.entry_price;
  const exit  = parseFloat(exitPrice) || 0;
  const pips  = exit > 0
    ? (trade.direction === "long" ? exit - entry : entry - exit)
    : 0;
  const pct   = entry > 0 ? (pips / entry) * 100 : 0;

  const mutation = useMutation({
    mutationFn: () =>
      journalApi.update(trade.id, {
        status:      outcome,
        exit_price:  parseFloat(exitPrice),
        pnl_pips:    parseFloat(pips.toFixed(5)),
        pnl_percent: parseFloat(pct.toFixed(4)),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["trades"] });
      onClose();
    },
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div
        className="bg-terminal-card border border-terminal-border rounded-xl w-full max-w-sm mx-4 shadow-2xl animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-terminal-border">
          <h2 className="font-semibold text-terminal-text flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-terminal-accent" />
            Close {trade.symbol} {trade.direction.toUpperCase()}
          </h2>
          <button onClick={onClose} className="text-terminal-muted hover:text-terminal-text">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-5 space-y-4">
          <label className="space-y-1 block">
            <span className="text-xs text-terminal-muted">Exit Price</span>
            <input
              type="number"
              step="any"
              placeholder={entry.toString()}
              value={exitPrice}
              onChange={(e) => setExitPrice(e.target.value)}
              className="w-full bg-terminal-secondary border border-terminal-border rounded-md px-3 py-2 text-sm text-terminal-text focus:outline-none focus:border-terminal-accent font-mono"
            />
          </label>

          {exit > 0 && (
            <div className="text-xs bg-terminal-bg px-3 py-2 rounded-md border border-terminal-border space-y-1">
              <div className="flex justify-between">
                <span className="text-terminal-muted">Pips</span>
                <span className={cn("font-mono", getPnlClass(pips))}>{pips > 0 ? "+" : ""}{pips.toFixed(5)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-terminal-muted">Return</span>
                <span className={cn("font-mono", getPnlClass(pct))}>{pct > 0 ? "+" : ""}{pct.toFixed(3)}%</span>
              </div>
            </div>
          )}

          <div className="space-y-1">
            <span className="text-xs text-terminal-muted">Outcome</span>
            <div className="flex gap-2">
              {(["win", "loss", "breakeven"] as const).map((o) => (
                <button
                  key={o}
                  onClick={() => setOutcome(o)}
                  className={cn(
                    "flex-1 py-1.5 rounded-md text-xs font-medium border transition-colors uppercase",
                    outcome === o
                      ? o === "win"
                        ? "bg-terminal-bull/20 border-terminal-bull text-terminal-bull"
                        : o === "loss"
                        ? "bg-terminal-bear/20 border-terminal-bear text-terminal-bear"
                        : "bg-terminal-muted/20 border-terminal-muted text-terminal-muted"
                      : "border-terminal-border text-terminal-muted hover:border-terminal-accent"
                  )}
                >
                  {o}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 px-5 py-4 border-t border-terminal-border">
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button
            variant={outcome === "win" ? "bull" : outcome === "loss" ? "bear" : "default"}
            disabled={!exitPrice || mutation.isPending}
            onClick={() => mutation.mutate()}
          >
            {mutation.isPending ? "Saving…" : "Close Trade"}
          </Button>
        </div>
      </div>
    </div>
  );
}

// ─── Stats Bar ────────────────────────────────────────────────────────────────

function StatsBar({ trades }: { trades: Trade[] }) {
  const closed  = trades.filter((t) => t.status !== "open");
  const wins    = closed.filter((t) => t.status === "win").length;
  const losses  = closed.filter((t) => t.status === "loss").length;
  const winRate = closed.length > 0 ? ((wins / closed.length) * 100).toFixed(1) : "—";

  const avgRR = (() => {
    const withRR = trades.filter((t) => t.stop_loss && t.take_profit && t.entry_price);
    if (!withRR.length) return "—";
    const avg = withRR.reduce((s, t) => {
      const risk   = Math.abs(t.entry_price - t.stop_loss);
      const reward = Math.abs(t.take_profit - t.entry_price);
      return s + (risk > 0 ? reward / risk : 0);
    }, 0) / withRR.length;
    return avg.toFixed(2);
  })();

  const netPct = closed.reduce((s, t) => s + (t.pnl_percent ?? 0), 0);

  const stats = [
    { label: "Total Trades", value: trades.length.toString() },
    { label: "Win Rate",     value: `${winRate}%`,   valueClass: parseFloat(winRate) >= 50 ? "text-terminal-bull" : "text-terminal-bear" },
    { label: "Avg R:R",      value: `1:${avgRR}`,    valueClass: parseFloat(avgRR) >= 2 ? "text-terminal-bull" : "text-terminal-warning" },
    { label: "Net P&L",      value: `${netPct >= 0 ? "+" : ""}${netPct.toFixed(2)}%`, valueClass: getPnlClass(netPct) },
    { label: "Open",         value: trades.filter((t) => t.status === "open").length.toString() },
    { label: "Wins / Losses", value: `${wins} / ${losses}` },
  ];

  return (
    <div className="grid grid-cols-3 lg:grid-cols-6 gap-3">
      {stats.map(({ label, value, valueClass }) => (
        <Card key={label}>
          <CardContent className="p-3">
            <p className="text-[10px] uppercase tracking-wider text-terminal-muted mb-1">{label}</p>
            <p className={cn("text-lg font-mono font-bold", valueClass ?? "text-terminal-text")}>{value}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function JournalPage() {
  const [filter, setFilter]         = useState<FilterStatus>("all");
  const [showAdd, setShowAdd]       = useState(false);
  const [closing, setClosing]       = useState<Trade | null>(null);
  const qc = useQueryClient();

  const { data: trades = [], isLoading, refetch } = useQuery<Trade[]>({
    queryKey: ["trades"],
    queryFn:  () => journalApi.list({ limit: 200 }).then((r) => r.data),
    refetchInterval: 30_000,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => journalApi.delete(id),
    onSuccess:  () => qc.invalidateQueries({ queryKey: ["trades"] }),
  });

  const filtered = filter === "all" ? trades : trades.filter((t) => t.status === filter);

  const FILTERS: { key: FilterStatus; label: string }[] = [
    { key: "all",       label: `All (${trades.length})` },
    { key: "open",      label: `Open (${trades.filter((t) => t.status === "open").length})` },
    { key: "win",       label: `Wins (${trades.filter((t) => t.status === "win").length})` },
    { key: "loss",      label: `Losses (${trades.filter((t) => t.status === "loss").length})` },
    { key: "breakeven", label: `BE (${trades.filter((t) => t.status === "breakeven").length})` },
  ];

  return (
    <div className="space-y-4 animate-slide-up">
      {/* Stats */}
      <StatsBar trades={trades} />

      {/* Table card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between flex-wrap gap-3">
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-terminal-accent" />
              Trade Journal
            </CardTitle>
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="icon" onClick={() => refetch()} title="Refresh">
                <RefreshCw className="w-3.5 h-3.5" />
              </Button>
              <Button variant="bull" onClick={() => setShowAdd(true)} className="gap-1.5">
                <Plus className="w-3.5 h-3.5" /> Log Trade
              </Button>
            </div>
          </div>

          {/* Filter tabs */}
          <div className="flex gap-1 mt-2 flex-wrap">
            {FILTERS.map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setFilter(key)}
                className={cn(
                  "px-3 py-1 rounded-full text-xs font-medium transition-colors",
                  filter === key
                    ? "bg-terminal-accent text-white"
                    : "text-terminal-muted hover:text-terminal-text hover:bg-terminal-hover"
                )}
              >
                {label}
              </button>
            ))}
          </div>
        </CardHeader>

        <CardContent className="p-0">
          {isLoading ? (
            <p className="text-sm text-terminal-muted text-center py-10">Loading trades…</p>
          ) : filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-terminal-muted">
              <BookOpen className="w-10 h-10 mb-3 opacity-20" />
              <p className="text-sm">No trades yet.</p>
              <button
                onClick={() => setShowAdd(true)}
                className="mt-3 text-xs text-terminal-accent hover:underline"
              >
                Log your first trade →
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-terminal-border text-terminal-muted">
                    <th className="text-left px-3 py-2 font-medium">#</th>
                    <th className="text-left px-3 py-2 font-medium">Symbol</th>
                    <th className="text-left px-3 py-2 font-medium">Dir</th>
                    <th className="text-right px-3 py-2 font-medium">Entry</th>
                    <th className="text-right px-3 py-2 font-medium">SL</th>
                    <th className="text-right px-3 py-2 font-medium">TP</th>
                    <th className="text-right px-3 py-2 font-medium hidden md:table-cell">R:R</th>
                    <th className="text-right px-3 py-2 font-medium hidden lg:table-cell">Exit</th>
                    <th className="text-right px-3 py-2 font-medium hidden md:table-cell">P&L %</th>
                    <th className="text-left px-3 py-2 font-medium">Status</th>
                    <th className="text-left px-3 py-2 font-medium hidden lg:table-cell">Strategy</th>
                    <th className="text-left px-3 py-2 font-medium hidden xl:table-cell">Date</th>
                    <th className="px-3 py-2" />
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((trade) => {
                    const risk   = Math.abs(trade.entry_price - trade.stop_loss);
                    const reward = Math.abs(trade.take_profit - trade.entry_price);
                    const rr     = risk > 0 ? (reward / risk).toFixed(1) : "—";
                    const pnlPct = trade.pnl_percent ?? 0;
                    const decimals = trade.symbol === "BTCUSDT" || trade.symbol === "US100" ? 2 : 5;

                    return (
                      <tr
                        key={trade.id}
                        className="border-b border-terminal-border/50 hover:bg-terminal-hover transition-colors group"
                      >
                        <td className="px-3 py-2.5 text-terminal-muted">{trade.id}</td>
                        <td className="px-3 py-2.5 font-semibold">{trade.symbol}</td>
                        <td className="px-3 py-2.5">{dirBadge(trade.direction)}</td>
                        <td className="px-3 py-2.5 text-right font-mono">{formatPrice(trade.entry_price, decimals)}</td>
                        <td className="px-3 py-2.5 text-right font-mono text-terminal-bear">{formatPrice(trade.stop_loss, decimals)}</td>
                        <td className="px-3 py-2.5 text-right font-mono text-terminal-bull">{formatPrice(trade.take_profit, decimals)}</td>
                        <td className="px-3 py-2.5 text-right font-mono hidden md:table-cell">1:{rr}</td>
                        <td className="px-3 py-2.5 text-right font-mono hidden lg:table-cell text-terminal-muted">
                          {trade.exit_price ? formatPrice(trade.exit_price, decimals) : "—"}
                        </td>
                        <td className={cn("px-3 py-2.5 text-right font-mono hidden md:table-cell", getPnlClass(pnlPct))}>
                          {trade.pnl_percent != null
                            ? `${pnlPct >= 0 ? "+" : ""}${pnlPct.toFixed(2)}%`
                            : "—"}
                        </td>
                        <td className="px-3 py-2.5">{statusBadge(trade.status)}</td>
                        <td className="px-3 py-2.5 hidden lg:table-cell text-terminal-muted">
                          {trade.strategy ?? "—"}
                        </td>
                        <td className="px-3 py-2.5 hidden xl:table-cell text-terminal-muted whitespace-nowrap">
                          {new Date(trade.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-3 py-2.5">
                          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            {trade.status === "open" && (
                              <Button
                                size="icon"
                                variant="ghost"
                                className="w-6 h-6 hover:text-terminal-bull hover:bg-terminal-bull/10"
                                title="Close trade"
                                onClick={() => setClosing(trade)}
                              >
                                <CheckCircle className="w-3 h-3" />
                              </Button>
                            )}
                            <Button
                              size="icon"
                              variant="ghost"
                              className="w-6 h-6 hover:text-terminal-bear hover:bg-terminal-bear/10"
                              title="Delete"
                              onClick={() => {
                                if (confirm(`Delete trade #${trade.id}?`)) {
                                  deleteMutation.mutate(trade.id);
                                }
                              }}
                            >
                              <Trash2 className="w-3 h-3" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modals */}
      {showAdd  && <AddTradeModal onClose={() => setShowAdd(false)} />}
      {closing  && <CloseTradeModal trade={closing} onClose={() => setClosing(null)} />}
    </div>
  );
}
