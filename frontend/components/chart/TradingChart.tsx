"use client";

import { useEffect, useRef, useCallback } from "react";
import type { OHLCVCandle } from "@/hooks/useChartData";

interface TradingChartProps {
  candles: OHLCVCandle[];
  symbol: string;
  timeframe: string;
  height?: number;
}

export function TradingChart({ candles, symbol, timeframe, height = 480 }: TradingChartProps) {
  const containerRef    = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const chartRef        = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const candleSeriesRef = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const emaSeriesRef    = useRef<any>(null);
  // Bridge async init gap: always holds the latest candles prop value
  const latestCandlesRef = useRef<OHLCVCandle[]>([]);
  latestCandlesRef.current = candles;

  const applyCandles = useCallback((data: OHLCVCandle[]) => {
    if (!candleSeriesRef.current || data.length === 0) return;
    const sorted = [...data].sort((a, b) => a.time - b.time);
    candleSeriesRef.current.setData(sorted);
    if (emaSeriesRef.current) {
      emaSeriesRef.current[0].setData(computeEMA(sorted, 20));
      emaSeriesRef.current[1].setData(computeEMA(sorted, 50));
    }
    chartRef.current?.timeScale().fitContent();
  }, []);

  const initChart = useCallback(async () => {
    if (!containerRef.current) return;

    const { createChart, CrosshairMode, ColorType } = await import("lightweight-charts");

    // Guard against unmount during the dynamic import
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      width:  containerRef.current.clientWidth,
      height,
      layout: {
        background: { type: ColorType.Solid, color: "#0d1117" },
        textColor:  "#8b949e",
        fontSize:   11,
      },
      grid: {
        vertLines: { color: "#21262d", style: 1 },
        horzLines: { color: "#21262d", style: 1 },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: { color: "#484f58", width: 1, style: 2 },
        horzLine: { color: "#484f58", width: 1, style: 2 },
      },
      rightPriceScale: {
        borderColor:   "#30363d",
        scaleMargins:  { top: 0.1, bottom: 0.2 },
      },
      timeScale: {
        borderColor:    "#30363d",
        timeVisible:    true,
        secondsVisible: false,
      },
    });

    const candleSeries = chart.addCandlestickSeries({
      upColor:         "#238636",
      downColor:       "#da3633",
      borderUpColor:   "#238636",
      borderDownColor: "#da3633",
      wickUpColor:     "#2ea043",
      wickDownColor:   "#f85149",
    });

    const emaSeries = chart.addLineSeries({
      color:            "#58a6ff",
      lineWidth:        1,
      priceLineVisible: false,
      lastValueVisible: false,
    });

    const ema50Series = chart.addLineSeries({
      color:            "#d29922",
      lineWidth:        1,
      priceLineVisible: false,
      lastValueVisible: false,
    });

    chartRef.current        = chart;
    candleSeriesRef.current = candleSeries;
    emaSeriesRef.current    = [emaSeries, ema50Series];

    // Apply any candles that arrived before init resolved
    if (latestCandlesRef.current.length > 0) {
      applyCandles(latestCandlesRef.current);
    }

    const ro = new ResizeObserver(() => {
      chart.applyOptions({ width: containerRef.current?.clientWidth ?? 600 });
    });
    ro.observe(containerRef.current);

    return () => {
      ro.disconnect();
      chart.remove();
    };
  }, [height, applyCandles]);

  // Init chart once on mount
  useEffect(() => {
    let cleanup: (() => void) | undefined;
    initChart().then((fn) => { cleanup = fn; });
    return () => {
      cleanup?.();
      chartRef.current        = null;
      candleSeriesRef.current = null;
      emaSeriesRef.current    = null;
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Apply candles on every update (handles both post-init and symbol changes)
  useEffect(() => {
    applyCandles(candles);
  }, [candles, applyCandles]);

  return (
    <div
      className="relative w-full bg-terminal-bg rounded-lg overflow-hidden border border-terminal-border"
      style={{ height }}
    >
      <div className="absolute top-3 left-3 z-10 flex items-center gap-2">
        <span className="font-mono text-sm font-bold text-terminal-text bg-terminal-card/90 px-2 py-0.5 rounded">
          {symbol}
        </span>
        <span className="text-xs text-terminal-muted bg-terminal-card/90 px-1.5 py-0.5 rounded">
          {timeframe}
        </span>
      </div>
      <div className="absolute top-3 right-3 z-10 flex items-center gap-3 text-[10px] bg-terminal-card/90 px-2 py-1 rounded">
        <span className="flex items-center gap-1">
          <span className="w-3 h-0.5 bg-terminal-accent inline-block" /> EMA 20
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-0.5 bg-terminal-warning inline-block" /> EMA 50
        </span>
      </div>
      <div ref={containerRef} className="w-full h-full" />
    </div>
  );
}

function computeEMA(
  candles: OHLCVCandle[],
  period: number,
): { time: number; value: number }[] {
  const k      = 2 / (period + 1);
  const result: { time: number; value: number }[] = [];
  let ema      = 0;

  for (let i = 0; i < candles.length; i++) {
    const price = candles[i].close;
    if (i < period - 1) {
      continue;
    } else if (i === period - 1) {
      ema = candles.slice(0, period).reduce((s, c) => s + c.close, 0) / period;
    } else {
      ema = price * k + ema * (1 - k);
    }
    result.push({ time: candles[i].time, value: Math.round(ema * 1e5) / 1e5 });
  }
  return result;
}
