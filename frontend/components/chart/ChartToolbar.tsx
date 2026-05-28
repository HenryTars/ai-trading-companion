"use client";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { RefreshCw } from "lucide-react";

const TIMEFRAMES = ["M15", "H1", "H4", "D1", "W1"];
const SYMBOLS    = ["XAUUSD", "EURUSD", "GBPUSD", "BTCUSDT", "US100"];

interface ChartToolbarProps {
  symbol:    string;
  timeframe: string;
  loading?:  boolean;
  onSymbol:    (s: string) => void;
  onTimeframe: (tf: string) => void;
  onRefresh:   () => void;
}

export function ChartToolbar({
  symbol, timeframe, loading,
  onSymbol, onTimeframe, onRefresh,
}: ChartToolbarProps) {
  return (
    <div className="flex items-center gap-3 flex-wrap">
      {/* Symbol pills */}
      <div className="flex items-center gap-1 bg-terminal-secondary rounded-lg p-1">
        {SYMBOLS.map((s) => (
          <button
            key={s}
            onClick={() => onSymbol(s)}
            className={cn(
              "px-2.5 py-1 rounded-md text-xs font-semibold transition-colors",
              symbol === s
                ? "bg-terminal-accent text-white"
                : "text-terminal-muted hover:text-terminal-text hover:bg-terminal-hover"
            )}
          >
            {s}
          </button>
        ))}
      </div>

      <div className="w-px h-5 bg-terminal-border" />

      {/* Timeframe pills */}
      <div className="flex items-center gap-1 bg-terminal-secondary rounded-lg p-1">
        {TIMEFRAMES.map((tf) => (
          <button
            key={tf}
            onClick={() => onTimeframe(tf)}
            className={cn(
              "px-2.5 py-1 rounded-md text-xs font-semibold transition-colors",
              timeframe === tf
                ? "bg-terminal-card border border-terminal-accent/40 text-terminal-accent"
                : "text-terminal-muted hover:text-terminal-text hover:bg-terminal-hover"
            )}
          >
            {tf}
          </button>
        ))}
      </div>

      <div className="ml-auto">
        <Button size="icon" variant="ghost" className="w-7 h-7" onClick={onRefresh}>
          <RefreshCw className={cn("w-3.5 h-3.5", loading && "animate-spin")} />
        </Button>
      </div>
    </div>
  );
}
