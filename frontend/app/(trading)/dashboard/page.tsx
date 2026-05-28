"use client";

import { useQuery } from "@tanstack/react-query";
import { AccountPanel } from "@/components/dashboard/AccountPanel";
import { WatchlistTable } from "@/components/dashboard/WatchlistTable";
import { PositionsTable } from "@/components/dashboard/PositionsTable";
import { SignalCard } from "@/components/dashboard/SignalCard";
import { ConnectionStatus } from "@/components/status/ConnectionStatus";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { signalApi } from "@/services/api";
import { useAppStore, useMT5Store } from "@/store";
import { formatCurrency, getPnlClass, cn } from "@/lib/utils";
import type { AISignal } from "@/types";
import { Activity, Bot } from "lucide-react";

function AISignalsFeed() {
  const { data: signals = [], refetch } = useQuery<AISignal[]>({
    queryKey: ["signals"],
    queryFn: () => signalApi.list().then((r) => r.data),
    refetchInterval: 30_000,
  });

  async function handleApprove(id: string) {
    await signalApi.approve(id);
    refetch();
  }
  async function handleReject(id: string) {
    await signalApi.reject(id);
    refetch();
  }

  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Bot className="w-3.5 h-3.5 text-terminal-accent" />
            AI Signals
          </CardTitle>
          <Badge variant={signals.length > 0 ? "default" : "muted"}>
            {signals.length} active
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="flex-1 overflow-auto space-y-2 p-3 pt-0">
        {signals.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 text-terminal-muted">
            <Activity className="w-8 h-8 mb-2 opacity-30" />
            <p className="text-sm">Scanning markets…</p>
          </div>
        ) : (
          signals.slice(0, 5).map((sig) => (
            <SignalCard
              key={sig.id}
              signal={sig}
              onApprove={handleApprove}
              onReject={handleReject}
              compact
            />
          ))
        )}
      </CardContent>
    </Card>
  );
}

function FloatingPnLBar() {
  const { positions, account } = useMT5Store();
  if (!account || positions.length === 0) return null;

  const totalPnl = positions.reduce((s, p) => s + p.pnl, 0);
  const pnlClass = getPnlClass(totalPnl);

  return (
    <div className={cn(
      "fixed bottom-4 right-4 px-4 py-2 rounded-lg border bg-terminal-card shadow-lg flex items-center gap-3 z-50",
      totalPnl >= 0 ? "border-terminal-bull/30 glow-bull" : "border-terminal-bear/30 glow-bear"
    )}>
      <span className="text-xs text-terminal-muted">Live P&L</span>
      <span className={cn("font-mono font-bold", pnlClass)}>
        {formatCurrency(totalPnl)}
      </span>
      <span className="text-xs text-terminal-muted">{positions.length} pos.</span>
    </div>
  );
}

export default function DashboardPage() {
  const { systemStatus } = useAppStore();
  const { status: mt5 } = useMT5Store();
  const isReady = systemStatus?.backend;

  if (!isReady) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 mx-auto rounded-full bg-terminal-card border border-terminal-border flex items-center justify-center">
            <Activity className="w-8 h-8 text-terminal-accent animate-pulse" />
          </div>
          <p className="text-terminal-muted text-sm">Connecting to backend…</p>
          <ConnectionStatus />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 animate-slide-up">
      {/* Account metrics */}
      <AccountPanel />

      {/* Main grid */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 min-h-0">
        {/* Left: Positions + Watchlist */}
        <div className="xl:col-span-2 space-y-4">
          <PositionsTable />
          <WatchlistTable />
        </div>

        {/* Right: AI Signals */}
        <div className="min-h-[400px]">
          <AISignalsFeed />
        </div>
      </div>

      {/* Status panel when MT5 offline */}
      {!mt5.connected && (
        <div className="flex justify-center">
          <ConnectionStatus />
        </div>
      )}

      <FloatingPnLBar />
    </div>
  );
}
