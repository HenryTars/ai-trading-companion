"use client";

import { useEffect, useRef, useCallback } from "react";

export interface EquityPoint {
  time: string;  // "YYYY-MM-DD"
  value: number; // cumulative P&L %
}

interface EquityCurveProps {
  data: EquityPoint[];
  height?: number;
}

export function EquityCurve({ data, height = 220 }: EquityCurveProps) {
  const containerRef  = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const chartRef      = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const seriesRef     = useRef<any>(null);
  const latestDataRef = useRef<EquityPoint[]>([]);
  latestDataRef.current = data;

  const applyData = useCallback((pts: EquityPoint[]) => {
    if (!seriesRef.current || pts.length === 0) return;
    seriesRef.current.setData(pts);
    chartRef.current?.timeScale().fitContent();
  }, []);

  const initChart = useCallback(async () => {
    if (!containerRef.current) return;

    const { createChart, ColorType, LineStyle } = await import("lightweight-charts");
    if (!containerRef.current) return;

    const lastVal   = latestDataRef.current.at(-1)?.value ?? 0;
    const lineColor = lastVal >= 0 ? "#238636" : "#da3633";
    const topColor  = lastVal >= 0 ? "rgba(35,134,54,0.25)"  : "rgba(218,54,51,0.25)";
    const btmColor  = lastVal >= 0 ? "rgba(35,134,54,0.02)"  : "rgba(218,54,51,0.02)";

    const chart = createChart(containerRef.current, {
      width:  containerRef.current.clientWidth,
      height,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor:  "#8b949e",
        fontSize:   11,
      },
      grid: {
        vertLines: { color: "#21262d", style: LineStyle.Dotted },
        horzLines: { color: "#21262d", style: LineStyle.Dotted },
      },
      rightPriceScale: {
        borderColor:  "#30363d",
        scaleMargins: { top: 0.1, bottom: 0.1 },
      },
      timeScale: {
        borderColor: "#30363d",
        timeVisible: true,
      },
      crosshair: {
        vertLine: { color: "#484f58", style: LineStyle.Dashed },
        horzLine: { color: "#484f58", style: LineStyle.Dashed },
      },
    });

    const series = chart.addAreaSeries({
      lineColor,
      topColor,
      bottomColor:      btmColor,
      lineWidth:        2,
      priceLineVisible: false,
      lastValueVisible: true,
      crosshairMarkerVisible: true,
    });

    chartRef.current = chart;
    seriesRef.current = series;

    if (latestDataRef.current.length > 0) {
      applyData(latestDataRef.current);
    }

    const ro = new ResizeObserver(() => {
      chart.applyOptions({ width: containerRef.current?.clientWidth ?? 600 });
    });
    ro.observe(containerRef.current);

    return () => { ro.disconnect(); chart.remove(); };
  }, [height, applyData]);

  useEffect(() => {
    let cleanup: (() => void) | undefined;
    initChart().then((fn) => { cleanup = fn; });
    return () => {
      cleanup?.();
      chartRef.current = null;
      seriesRef.current = null;
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => { applyData(data); }, [data, applyData]);

  if (data.length === 0) {
    return (
      <div
        className="flex items-center justify-center text-terminal-muted text-sm"
        style={{ height }}
      >
        No closed trades yet — equity curve will appear here.
      </div>
    );
  }

  return <div ref={containerRef} className="w-full" style={{ height }} />;
}
