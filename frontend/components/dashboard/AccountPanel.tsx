"use client";

import { useMT5Store } from "@/store";
import { Card, CardContent } from "@/components/ui/card";
import { formatCurrency, formatPercent, getPnlClass, cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, DollarSign, Shield } from "lucide-react";

function MetricCard({
  label,
  value,
  subValue,
  icon: Icon,
  valueClass,
}: {
  label: string;
  value: string;
  subValue?: string;
  icon: React.ElementType;
  valueClass?: string;
}) {
  return (
    <Card className="flex-1 min-w-0">
      <CardContent className="p-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="text-[10px] uppercase tracking-wider text-terminal-muted mb-1">{label}</p>
            <p className={cn("text-xl font-mono font-bold truncate", valueClass ?? "text-terminal-text")}>
              {value}
            </p>
            {subValue && (
              <p className="text-xs text-terminal-muted mt-0.5">{subValue}</p>
            )}
          </div>
          <div className="w-8 h-8 rounded-md bg-terminal-secondary flex items-center justify-center shrink-0">
            <Icon className="w-4 h-4 text-terminal-muted" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function AccountPanel() {
  const { account, positions, status } = useMT5Store();

  if (!status.connected || !account) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {["Balance", "Equity", "Floating P&L", "Margin Used"].map((label) => (
          <Card key={label} className="flex-1">
            <CardContent className="p-3">
              <p className="text-[10px] uppercase tracking-wider text-terminal-muted mb-1">{label}</p>
              <p className="text-xl font-mono font-bold text-terminal-muted">---</p>
              <p className="text-xs text-terminal-muted mt-0.5">MT5 not connected</p>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const floatClass = getPnlClass(account.floating_pnl);
  const equityClass = account.equity >= account.balance ? "text-terminal-bull" : "text-terminal-bear";
  const marginPct = account.margin > 0 ? ((account.margin / account.equity) * 100) : 0;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      <MetricCard
        label="Balance"
        value={formatCurrency(account.balance)}
        subValue={`${account.currency} · ${account.leverage}:1`}
        icon={DollarSign}
      />
      <MetricCard
        label="Equity"
        value={formatCurrency(account.equity)}
        subValue={formatPercent((account.equity - account.balance) / account.balance * 100)}
        icon={TrendingUp}
        valueClass={equityClass}
      />
      <MetricCard
        label="Floating P&L"
        value={formatCurrency(account.floating_pnl)}
        subValue={`${positions.length} open position${positions.length !== 1 ? "s" : ""}`}
        icon={account.floating_pnl >= 0 ? TrendingUp : TrendingDown}
        valueClass={floatClass}
      />
      <MetricCard
        label="Margin Used"
        value={formatCurrency(account.margin)}
        subValue={`${marginPct.toFixed(1)}% · Free: ${formatCurrency(account.free_margin)}`}
        icon={Shield}
      />
    </div>
  );
}
