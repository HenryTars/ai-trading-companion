"use client";

import { useMT5Store } from "@/store";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatCurrency, formatPips, getPnlClass, cn } from "@/lib/utils";
import { mt5Api } from "@/services/api";
import { X } from "lucide-react";

export function PositionsTable() {
  const { positions, removePosition } = useMT5Store();

  async function handleClose(ticket: number) {
    try {
      await mt5Api.closePosition(ticket);
      removePosition(ticket);
    } catch (e) {
      console.error("Close failed", e);
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Open Positions</CardTitle>
          <Badge variant={positions.length > 0 ? "default" : "muted"}>
            {positions.length}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        {positions.length === 0 ? (
          <p className="text-sm text-terminal-muted text-center py-6">No open positions</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-terminal-border text-terminal-muted">
                  <th className="text-left px-3 py-2 font-medium">Symbol</th>
                  <th className="text-left px-3 py-2 font-medium">Type</th>
                  <th className="text-right px-3 py-2 font-medium">Vol</th>
                  <th className="text-right px-3 py-2 font-medium">Entry</th>
                  <th className="text-right px-3 py-2 font-medium">Current</th>
                  <th className="text-right px-3 py-2 font-medium">Pips</th>
                  <th className="text-right px-3 py-2 font-medium">P&L</th>
                  <th className="px-3 py-2" />
                </tr>
              </thead>
              <tbody>
                {positions.map((pos) => (
                  <tr
                    key={pos.ticket}
                    className="border-b border-terminal-border/50 hover:bg-terminal-hover transition-colors"
                  >
                    <td className="px-3 py-2 font-semibold">{pos.symbol}</td>
                    <td className="px-3 py-2">
                      <Badge variant={pos.type === "BUY" ? "bull" : "bear"} className="text-[10px]">
                        {pos.type}
                      </Badge>
                    </td>
                    <td className="px-3 py-2 text-right font-mono">{pos.volume.toFixed(2)}</td>
                    <td className="px-3 py-2 text-right font-mono">{pos.open_price.toFixed(5)}</td>
                    <td className="px-3 py-2 text-right font-mono">{pos.current_price.toFixed(5)}</td>
                    <td className={cn("px-3 py-2 text-right font-mono", getPnlClass(pos.pips))}>
                      {formatPips(pos.pips)}
                    </td>
                    <td className={cn("px-3 py-2 text-right font-mono font-semibold", getPnlClass(pos.pnl))}>
                      {formatCurrency(pos.pnl)}
                    </td>
                    <td className="px-3 py-2">
                      <Button
                        size="icon"
                        variant="ghost"
                        className="w-6 h-6 hover:text-terminal-bear hover:bg-terminal-bear/10"
                        onClick={() => handleClose(pos.ticket)}
                      >
                        <X className="w-3 h-3" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="border-t border-terminal-border">
                  <td colSpan={6} className="px-3 py-2 text-terminal-muted">Total P&L</td>
                  <td className={cn("px-3 py-2 text-right font-mono font-bold text-sm",
                    getPnlClass(positions.reduce((sum, p) => sum + p.pnl, 0)))}>
                    {formatCurrency(positions.reduce((sum, p) => sum + p.pnl, 0))}
                  </td>
                  <td />
                </tr>
              </tfoot>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
