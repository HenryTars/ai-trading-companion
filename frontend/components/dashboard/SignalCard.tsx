"use client";

import { motion } from "framer-motion";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getBiasColor, getConfidenceColor, formatPrice, cn } from "@/lib/utils";
import type { AISignal } from "@/types";
import { CheckCircle, XCircle, TrendingUp, TrendingDown } from "lucide-react";

interface Props {
  signal: AISignal;
  onApprove?: (id: string) => void;
  onReject?: (id: string) => void;
  compact?: boolean;
}

const GRADE_COLORS: Record<string, string> = {
  A: "text-terminal-bull border-terminal-bull/40 bg-terminal-bull/10",
  B: "text-terminal-accent border-terminal-accent/40 bg-terminal-accent/10",
  C: "text-terminal-warning border-terminal-warning/40 bg-terminal-warning/10",
  D: "text-terminal-muted border-terminal-border bg-terminal-hover",
  F: "text-terminal-bear border-terminal-bear/40 bg-terminal-bear/10",
};

export function SignalCard({ signal, onApprove, onReject, compact = false }: Props) {
  const isBull = signal.bias === "bullish";

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
    >
      <Card className={cn(
        "card-hover border",
        isBull ? "border-terminal-bull/20" : "border-terminal-bear/20"
      )}>
        <CardContent className="p-3">
          <div className="flex items-start justify-between gap-2 mb-2">
            <div className="flex items-center gap-2">
              {isBull
                ? <TrendingUp className="w-4 h-4 text-terminal-bull" />
                : <TrendingDown className="w-4 h-4 text-terminal-bear" />}
              <span className="font-semibold text-sm">{signal.symbol}</span>
              <Badge variant="muted" className="text-[10px]">{signal.timeframe}</Badge>
            </div>
            <div className={cn(
              "w-7 h-7 rounded border text-xs font-bold flex items-center justify-center",
              GRADE_COLORS[signal.grade] ?? GRADE_COLORS.F
            )}>
              {signal.grade}
            </div>
          </div>

          <div className="grid grid-cols-3 gap-2 mb-2 text-xs">
            <div>
              <p className="text-terminal-muted">Entry</p>
              <p className="font-mono font-semibold">{formatPrice(signal.entry_zone[0])}</p>
            </div>
            <div>
              <p className="text-terminal-muted">Stop Loss</p>
              <p className="font-mono text-terminal-bear">{formatPrice(signal.stop_loss)}</p>
            </div>
            <div>
              <p className="text-terminal-muted">Take Profit</p>
              <p className="font-mono text-terminal-bull">{formatPrice(signal.take_profit)}</p>
            </div>
          </div>

          <div className="flex items-center gap-3 mb-2">
            <span className={cn("text-xs font-semibold", getBiasColor(signal.bias))}>
              ● {signal.bias.toUpperCase()}
            </span>
            <span className={cn("text-xs", getConfidenceColor(signal.confidence))}>
              {(signal.confidence * 100).toFixed(0)}% confidence
            </span>
            <span className="text-xs text-terminal-muted ml-auto">
              R:R {signal.risk_reward.toFixed(1)}
            </span>
          </div>

          {!compact && signal.narrative && (
            <p className="text-xs text-terminal-muted line-clamp-2 mb-2">
              {signal.narrative}
            </p>
          )}

          {(onApprove || onReject) && (
            <div className="flex gap-2 mt-2">
              {onApprove && (
                <Button
                  size="sm"
                  variant="bull"
                  className="flex-1 h-7 text-xs gap-1"
                  onClick={() => onApprove(signal.id)}
                >
                  <CheckCircle className="w-3 h-3" /> Execute
                </Button>
              )}
              {onReject && (
                <Button
                  size="sm"
                  variant="outline"
                  className="flex-1 h-7 text-xs gap-1"
                  onClick={() => onReject(signal.id)}
                >
                  <XCircle className="w-3 h-3" /> Reject
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
