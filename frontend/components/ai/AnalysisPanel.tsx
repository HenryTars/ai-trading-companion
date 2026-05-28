"use client";

import { useQuery } from "@tanstack/react-query";
import { marketApi } from "@/services/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getBiasColor, getConfidenceColor, cn } from "@/lib/utils";
import { Bot, RefreshCw, TrendingUp, Activity } from "lucide-react";
import type { MarketAnalysis } from "@/types";

interface Props {
  symbol:    string;
  timeframe: string;
}

function IndicatorRow({ label, value, signal }: { label: string; value: string; signal?: "bull" | "bear" | "neutral" }) {
  const color = signal === "bull" ? "text-terminal-bull" : signal === "bear" ? "text-terminal-bear" : "text-terminal-text";
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-terminal-border/40 last:border-0">
      <span className="text-xs text-terminal-muted">{label}</span>
      <span className={cn("text-xs font-mono font-semibold", color)}>{value}</span>
    </div>
  );
}

function ConfidenceMeter({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = pct >= 70 ? "bg-terminal-bull" : pct >= 50 ? "bg-terminal-warning" : "bg-terminal-bear";
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-terminal-muted">Confidence</span>
        <span className={cn("font-mono font-bold", getConfidenceColor(value))}>{pct}%</span>
      </div>
      <div className="h-1.5 bg-terminal-secondary rounded-full overflow-hidden">
        <div className={cn("h-full rounded-full transition-all duration-500", color)} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export function AnalysisPanel({ symbol, timeframe }: Props) {
  const { data, isFetching, refetch } = useQuery<MarketAnalysis>({
    queryKey: ["analysis", symbol, timeframe],
    queryFn:  () => marketApi.analysis(symbol, timeframe).then((r) => r.data),
    staleTime: 120_000,
    retry: 1,
  });

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Bot className="w-3.5 h-3.5 text-terminal-accent" />
            AI Analysis
          </CardTitle>
          <Button size="icon" variant="ghost" className="w-6 h-6" onClick={() => refetch()}>
            <RefreshCw className={cn("w-3 h-3", isFetching && "animate-spin")} />
          </Button>
        </div>
        <p className="text-[10px] text-terminal-muted">{symbol} · {timeframe}</p>
      </CardHeader>

      <CardContent className="flex-1 overflow-auto p-3 pt-0 space-y-3">
        {!data ? (
          <div className="flex flex-col items-center justify-center h-32 text-terminal-muted">
            <Activity className="w-8 h-8 mb-2 opacity-30" />
            <p className="text-xs">{isFetching ? "Analysing…" : "No analysis yet"}</p>
          </div>
        ) : (
          <>
            {/* Bias + Confidence */}
            <div className="bg-terminal-secondary rounded-lg p-3 space-y-3">
              <div className="flex items-center justify-between">
                <span className={cn("text-sm font-bold uppercase", getBiasColor(data.bias))}>
                  ● {data.bias}
                </span>
                <div className="flex items-center gap-2">
                  <Badge variant={data.risk_level === "low" ? "bull" : data.risk_level === "high" ? "bear" : "warning"}>
                    {data.risk_level} risk
                  </Badge>
                  <Badge variant="muted">{data.trend_strength}</Badge>
                </div>
              </div>
              <ConfidenceMeter value={data.confidence} />
            </div>

            {/* Indicators */}
            <div className="bg-terminal-secondary rounded-lg p-3">
              <p className="text-[10px] text-terminal-muted uppercase tracking-wider mb-2">Indicators</p>
              <IndicatorRow
                label="RSI (14)"
                value={data.indicators.rsi.toFixed(1)}
                signal={data.indicators.rsi > 70 ? "bear" : data.indicators.rsi < 30 ? "bull" : "neutral"}
              />
              <IndicatorRow
                label="MACD"
                value={data.indicators.macd_signal}
                signal={data.indicators.macd_signal === "bullish" ? "bull" : "bear"}
              />
              <IndicatorRow
                label="ADX (14)"
                value={data.indicators.adx.toFixed(1)}
                signal={data.indicators.adx > 25 ? "bull" : "neutral"}
              />
              <IndicatorRow
                label="ATR (14)"
                value={data.indicators.atr.toFixed(4)}
              />
            </div>

            {/* Patterns */}
            {data.patterns_detected?.length > 0 && (
              <div>
                <p className="text-[10px] text-terminal-muted uppercase tracking-wider mb-1.5">Patterns</p>
                <div className="flex flex-wrap gap-1">
                  {data.patterns_detected.map((p, i) => (
                    <Badge key={i} variant="default" className="text-[10px]">{p}</Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Narrative */}
            <div className="bg-terminal-secondary rounded-lg p-3">
              <div className="flex items-center gap-1.5 mb-1.5">
                <TrendingUp className="w-3 h-3 text-terminal-accent" />
                <p className="text-[10px] text-terminal-muted uppercase tracking-wider">AI Narrative</p>
              </div>
              <p className="text-xs text-terminal-text-secondary leading-relaxed">{data.narrative}</p>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
