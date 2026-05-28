"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { mt5Api } from "@/services/api";
import { useMT5Store } from "@/store";
import { formatCurrency, cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, AlertCircle, CheckCircle2 } from "lucide-react";

interface Props {
  symbol:        string;
  currentPrice?: number;
  suggestedSL?:  number;
  suggestedTP?:  number;
}

type Result = { success: boolean; ticket?: number; price?: number; error?: string };

export function TradePanel({ symbol, currentPrice = 0, suggestedSL = 0, suggestedTP = 0 }: Props) {
  const { account, status } = useMT5Store();
  const [direction, setDirection] = useState<"BUY" | "SELL">("BUY");
  const [volume,    setVolume]    = useState("0.01");
  const [sl,        setSl]        = useState(suggestedSL.toFixed(5));
  const [tp,        setTp]        = useState(suggestedTP.toFixed(5));
  const [loading,   setLoading]   = useState(false);
  const [result,    setResult]    = useState<Result | null>(null);

  const slNum = parseFloat(sl) || 0;
  const tpNum = parseFloat(tp) || 0;
  const volNum = parseFloat(volume) || 0;

  // Compute R:R
  const risk   = Math.abs(currentPrice - slNum);
  const reward = Math.abs(tpNum - currentPrice);
  const rr     = risk > 0 ? reward / risk : 0;

  async function execute() {
    if (!status.connected) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await mt5Api.placeOrder({
        symbol,
        direction,
        volume:  volNum,
        sl:      slNum,
        tp:      tpNum,
        comment: "AI Terminal",
      });
      setResult({ success: true, ticket: res.data.ticket, price: res.data.price });
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Order failed";
      setResult({ success: false, error: msg });
    } finally {
      setLoading(false);
      setTimeout(() => setResult(null), 5000);
    }
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-xs">Quick Trade — {symbol}</CardTitle>
        {account && (
          <p className="text-[10px] text-terminal-muted">
            Balance: {formatCurrency(account.balance)} · Margin free: {formatCurrency(account.free_margin)}
          </p>
        )}
      </CardHeader>

      <CardContent className="p-3 pt-0 space-y-3">
        {!status.connected && (
          <p className="text-xs text-terminal-bear text-center py-2">MT5 not connected</p>
        )}

        {/* BUY / SELL toggle */}
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => setDirection("BUY")}
            className={cn(
              "py-2 rounded-md text-sm font-bold border transition-colors",
              direction === "BUY"
                ? "bg-terminal-bull text-white border-terminal-bull"
                : "border-terminal-border text-terminal-muted hover:border-terminal-bull/50"
            )}
          >
            <TrendingUp className="w-4 h-4 inline mr-1" /> BUY
          </button>
          <button
            onClick={() => setDirection("SELL")}
            className={cn(
              "py-2 rounded-md text-sm font-bold border transition-colors",
              direction === "SELL"
                ? "bg-terminal-bear text-white border-terminal-bear"
                : "border-terminal-border text-terminal-muted hover:border-terminal-bear/50"
            )}
          >
            <TrendingDown className="w-4 h-4 inline mr-1" /> SELL
          </button>
        </div>

        {/* Input fields */}
        <div className="space-y-2">
          {[
            { label: "Volume (lots)", value: volume,   setter: setVolume,   placeholder: "0.01" },
            { label: "Stop Loss",     value: sl,        setter: setSl,        placeholder: "0.00000" },
            { label: "Take Profit",   value: tp,        setter: setTp,        placeholder: "0.00000" },
          ].map(({ label, value, setter, placeholder }) => (
            <div key={label}>
              <label className="text-[10px] text-terminal-muted block mb-1">{label}</label>
              <input
                type="number"
                value={value}
                onChange={(e) => setter(e.target.value)}
                placeholder={placeholder}
                className="w-full bg-terminal-secondary border border-terminal-border rounded-md px-2.5 py-1.5 text-xs font-mono text-terminal-text focus:outline-none focus:border-terminal-accent"
              />
            </div>
          ))}
        </div>

        {/* R:R preview */}
        {rr > 0 && (
          <div className="flex items-center justify-between text-xs bg-terminal-secondary rounded-md px-2.5 py-1.5">
            <span className="text-terminal-muted">Risk : Reward</span>
            <Badge variant={rr >= 2 ? "bull" : rr >= 1 ? "warning" : "bear"}>
              1 : {rr.toFixed(1)}
            </Badge>
          </div>
        )}

        {/* Execute button */}
        <Button
          variant={direction === "BUY" ? "bull" : "bear"}
          className="w-full font-bold"
          disabled={loading || !status.connected || volNum <= 0}
          onClick={execute}
        >
          {loading ? "Placing…" : `${direction} ${volume} lot${parseFloat(volume) !== 1 ? "s" : ""} ${symbol}`}
        </Button>

        {/* Result feedback */}
        <AnimatePresence>
          {result && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className={cn(
                "flex items-center gap-2 text-xs p-2.5 rounded-md",
                result.success
                  ? "bg-terminal-bull/10 border border-terminal-bull/30 text-terminal-bull"
                  : "bg-terminal-bear/10 border border-terminal-bear/30 text-terminal-bear"
              )}
            >
              {result.success
                ? <><CheckCircle2 className="w-3.5 h-3.5 shrink-0" /> Ticket #{result.ticket} opened @ {result.price?.toFixed(5)}</>
                : <><AlertCircle className="w-3.5 h-3.5 shrink-0" /> {result.error}</>}
            </motion.div>
          )}
        </AnimatePresence>
      </CardContent>
    </Card>
  );
}
