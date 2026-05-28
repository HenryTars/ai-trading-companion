"use client";

import { useState } from "react";
import { TradingChart } from "@/components/chart/TradingChart";
import { ChartToolbar } from "@/components/chart/ChartToolbar";
import { AnalysisPanel } from "@/components/ai/AnalysisPanel";
import { TradePanel } from "@/components/trading/TradePanel";
import { PositionsTable } from "@/components/dashboard/PositionsTable";
import { useChartData } from "@/hooks/useChartData";
import { usePriceStore, useAppStore } from "@/store";
import { formatPrice, cn } from "@/lib/utils";
import { Card, CardContent } from "@/components/ui/card";

export default function ChartPage() {
  const { activeSymbol, activeTimeframe, setActiveSymbol, setActiveTimeframe } = useAppStore();
  const [symbol,    setSymbol]    = useState(activeSymbol);
  const [timeframe, setTimeframe] = useState(activeTimeframe);

  const { data: candles = [], isFetching, refetch } = useChartData(symbol, timeframe);
  const { ticks } = usePriceStore();
  const tick = ticks[symbol];

  function handleSymbol(s: string) {
    setSymbol(s);
    setActiveSymbol(s);
  }

  function handleTimeframe(tf: string) {
    setTimeframe(tf);
    setActiveTimeframe(tf);
  }

  // Last candle for current price if no live tick
  const lastCandle = candles[candles.length - 1];
  const currentPrice = tick?.bid ?? lastCandle?.close ?? 0;

  return (
    <div className="flex flex-col gap-3 h-full animate-slide-up">
      {/* Toolbar */}
      <ChartToolbar
        symbol={symbol}
        timeframe={timeframe}
        loading={isFetching}
        onSymbol={handleSymbol}
        onTimeframe={handleTimeframe}
        onRefresh={() => refetch()}
      />

      {/* Live price strip */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="text-2xl font-mono font-bold text-terminal-text">
            {currentPrice ? formatPrice(currentPrice, symbol.includes("BTC") || symbol === "US100" ? 2 : 5) : "---"}
          </span>
          {tick && (
            <span className="text-xs text-terminal-muted font-mono">
              Bid: {formatPrice(tick.bid, 5)} · Ask: {formatPrice(tick.ask, 5)} · Spread: {tick.spread?.toFixed(1)}
            </span>
          )}
        </div>
        {candles.length > 0 && (
          <span className="text-xs text-terminal-muted">{candles.length} candles</span>
        )}
      </div>

      {/* Main layout: chart + right panel */}
      <div className="flex gap-3 flex-1 min-h-0">
        {/* Chart area */}
        <div className="flex-1 flex flex-col gap-3 min-w-0">
          {candles.length === 0 && !isFetching ? (
            <Card className="flex-1 flex items-center justify-center">
              <CardContent>
                <p className="text-terminal-muted text-sm text-center">
                  {isFetching ? "Loading chart data…" : "No data available for this symbol/timeframe."}
                </p>
              </CardContent>
            </Card>
          ) : (
            <TradingChart
              candles={candles}
              symbol={symbol}
              timeframe={timeframe}
              height={460}
            />
          )}

          {/* Open positions below chart */}
          <PositionsTable />
        </div>

        {/* Right sidebar: Analysis + Trade */}
        <div className="w-72 shrink-0 flex flex-col gap-3 overflow-auto">
          <AnalysisPanel symbol={symbol} timeframe={timeframe} />
          <TradePanel
            symbol={symbol}
            currentPrice={currentPrice}
          />
        </div>
      </div>
    </div>
  );
}
