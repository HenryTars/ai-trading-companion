"use client";

import { useEffect, useState } from "react";
import { getSession, getSessionColor, formatTime } from "@/lib/utils";
import { useAppStore, useMT5Store, usePriceStore } from "@/store";
import { Badge } from "@/components/ui/badge";
import { Wifi, WifiOff, Clock } from "lucide-react";

const WATCHLIST_SYMBOLS = ["XAUUSD", "BTCUSDT", "EURUSD", "US100"];

function LiveClock() {
  const [time, setTime] = useState(() => new Date());
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  return (
    <span className="font-mono text-sm text-terminal-text-secondary">
      {formatTime(time)} UTC
    </span>
  );
}

function SessionBadge() {
  const session = getSession();
  const color = getSessionColor(session);
  return (
    <span className={`text-xs font-semibold ${color}`}>
      ● {session}
    </span>
  );
}

function PriceTicker() {
  const { ticks } = usePriceStore();
  return (
    <div className="hidden lg:flex items-center gap-4 border-l border-terminal-border pl-4">
      {WATCHLIST_SYMBOLS.map((sym) => {
        const tick = ticks[sym];
        return (
          <div key={sym} className="flex items-center gap-1.5">
            <span className="text-xs text-terminal-muted">{sym}</span>
            <span className="font-mono text-xs text-terminal-text">
              {tick ? tick.bid.toFixed(2) : "---"}
            </span>
          </div>
        );
      })}
    </div>
  );
}

export function Header({ title }: { title?: string }) {
  const { systemStatus } = useAppStore();
  const { status: mt5Status } = useMT5Store();

  const backendOk = systemStatus?.backend ?? false;

  return (
    <header className="h-14 border-b border-terminal-border bg-terminal-card flex items-center px-4 gap-4 shrink-0">
      {/* Page title */}
      <div className="flex-1">
        {title && (
          <h1 className="text-sm font-semibold text-terminal-text">{title}</h1>
        )}
      </div>

      {/* Price ticker */}
      <PriceTicker />

      {/* Session */}
      <div className="flex items-center gap-3 border-l border-terminal-border pl-4">
        <SessionBadge />
      </div>

      {/* Clock */}
      <div className="flex items-center gap-1.5 border-l border-terminal-border pl-4">
        <Clock className="w-3.5 h-3.5 text-terminal-muted" />
        <LiveClock />
      </div>

      {/* Status badges */}
      <div className="flex items-center gap-2 border-l border-terminal-border pl-4">
        <Badge variant={backendOk ? "bull" : "bear"} className="gap-1">
          {backendOk ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
          API
        </Badge>
        <Badge variant={mt5Status.connected ? "bull" : "bear"} className="gap-1">
          <span className={`w-1.5 h-1.5 rounded-full ${mt5Status.connected ? "bg-terminal-bull" : "bg-terminal-bear"}`} />
          MT5
        </Badge>
      </div>
    </header>
  );
}
