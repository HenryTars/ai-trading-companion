"use client";

import { useEffect, useRef, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { usePriceStore, useAppStore } from "@/store";
import { getPnlClass, cn } from "@/lib/utils";
import type { PriceTick } from "@/types";

const SYMBOLS = [
  { symbol: "XAUUSD",  display: "XAU/USD",  decimals: 2 },
  { symbol: "EURUSD",  display: "EUR/USD",  decimals: 5 },
  { symbol: "GBPUSD",  display: "GBP/USD",  decimals: 5 },
  { symbol: "BTCUSDT", display: "BTC/USDT", decimals: 0 },
  { symbol: "US100",   display: "NAS100",   decimals: 1 },
];

function PriceCell({ tick, decimals }: { tick?: PriceTick; decimals: number }) {
  const [flashClass, setFlashClass] = useState("");
  const prevRef = useRef<number | undefined>(undefined);

  useEffect(() => {
    if (!tick) return;
    const prev = prevRef.current;
    if (prev !== undefined && tick.bid !== prev) {
      setFlashClass(tick.bid > prev ? "price-up" : "price-down");
      const t = setTimeout(() => setFlashClass(""), 800);
      return () => clearTimeout(t);
    }
    prevRef.current = tick.bid;
  }, [tick?.bid]);

  return (
    <span className={cn("font-mono text-xs font-semibold transition-colors", flashClass)}>
      {tick ? tick.bid.toFixed(decimals) : "---"}
    </span>
  );
}

export function WatchlistTable() {
  const { ticks } = usePriceStore();
  const { setActiveSymbol, activeSymbol } = useAppStore();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Watchlist</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-terminal-border text-terminal-muted text-xs">
              <th className="text-left px-3 py-2 font-medium">Symbol</th>
              <th className="text-right px-3 py-2 font-medium">Bid</th>
              <th className="text-right px-3 py-2 font-medium">Ask</th>
              <th className="text-right px-3 py-2 font-medium hidden sm:table-cell">Spread</th>
            </tr>
          </thead>
          <tbody>
            {SYMBOLS.map(({ symbol, display, decimals }) => {
              const tick = ticks[symbol];

              return (
                <tr
                  key={symbol}
                  className={cn(
                    "border-b border-terminal-border/50 hover:bg-terminal-hover cursor-pointer transition-colors",
                    activeSymbol === symbol && "bg-terminal-accent/5 border-l-2 border-l-terminal-accent"
                  )}
                  onClick={() => setActiveSymbol(symbol)}
                >
                  <td className="px-3 py-2.5">
                    <div>
                      <p className="font-semibold text-xs">{display}</p>
                      <p className="text-[10px] text-terminal-muted">{symbol}</p>
                    </div>
                  </td>
                  <td className="px-3 py-2.5 text-right">
                    <PriceCell tick={tick} decimals={decimals} />
                  </td>
                  <td className="px-3 py-2.5 text-right">
                    <span className="font-mono text-xs text-terminal-muted">
                      {tick ? tick.ask.toFixed(decimals) : "---"}
                    </span>
                  </td>
                  <td className="px-3 py-2.5 text-right text-xs text-terminal-muted hidden sm:table-cell">
                    {tick?.spread?.toFixed(1) ?? "---"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}
