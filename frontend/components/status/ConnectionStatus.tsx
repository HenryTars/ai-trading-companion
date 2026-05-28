"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useAppStore, useMT5Store } from "@/store";
import { systemApi, mt5Api } from "@/services/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { RefreshCw, Server, Cpu, Database, Wifi } from "lucide-react";
import { cn } from "@/lib/utils";

interface StatusRowProps {
  icon: React.ElementType;
  label: string;
  status: boolean;
  detail?: string;
}

function StatusRow({ icon: Icon, label, status, detail }: StatusRowProps) {
  return (
    <div className="flex items-center gap-3 py-2 border-b border-terminal-border last:border-0">
      <div className={cn(
        "w-8 h-8 rounded-md flex items-center justify-center",
        status ? "bg-terminal-bull/10" : "bg-terminal-bear/10"
      )}>
        <Icon className={cn("w-4 h-4", status ? "text-terminal-bull" : "text-terminal-bear")} />
      </div>
      <div className="flex-1">
        <p className="text-sm font-medium">{label}</p>
        {detail && <p className="text-xs text-terminal-muted">{detail}</p>}
      </div>
      <div className="flex items-center gap-1.5">
        <span className={cn(
          "w-2 h-2 rounded-full pulse-dot",
          status ? "bg-terminal-bull" : "bg-terminal-bear"
        )} />
        <span className={cn("text-xs font-semibold", status ? "text-terminal-bull" : "text-terminal-bear")}>
          {status ? "Online" : "Offline"}
        </span>
      </div>
    </div>
  );
}

export function ConnectionStatus() {
  const { systemStatus, setSystemStatus } = useAppStore();
  const { status: mt5Status, setStatus: setMT5Status } = useMT5Store();
  const [refreshing, setRefreshing] = useState(false);

  async function refresh() {
    setRefreshing(true);
    try {
      const [statusRes, mt5Res] = await Promise.allSettled([
        systemApi.status(),
        mt5Api.status(),
      ]);
      if (statusRes.status === "fulfilled") setSystemStatus(statusRes.value.data);
      if (mt5Res.status === "fulfilled") setMT5Status(mt5Res.value.data);
    } finally {
      setRefreshing(false);
    }
  }

  async function connectMT5() {
    try {
      const res = await mt5Api.connect();
      setMT5Status(res.data);
    } catch (e) {
      console.error("MT5 connect failed", e);
    }
  }

  return (
    <Card className="w-full max-w-md">
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-terminal-muted">
            System Status
          </h3>
          <Button size="icon" variant="ghost" className="w-7 h-7" onClick={refresh}>
            <RefreshCw className={cn("w-3.5 h-3.5", refreshing && "animate-spin")} />
          </Button>
        </div>

        <StatusRow
          icon={Server}
          label="Backend API"
          status={systemStatus?.backend ?? false}
          detail={systemStatus ? `v${systemStatus.version}` : "Connecting..."}
        />
        <StatusRow
          icon={Wifi}
          label="MT5 Terminal"
          status={mt5Status.connected}
          detail={mt5Status.connected ? mt5Status.broker ?? "Connected" : mt5Status.reason ?? "Not connected"}
        />
        <StatusRow
          icon={Database}
          label="Database"
          status={systemStatus?.database ?? false}
          detail="SQLite"
        />
        <StatusRow
          icon={Cpu}
          label="AI Engine"
          status={systemStatus?.ai_engine ?? false}
          detail="Analysis ready"
        />

        {!mt5Status.connected && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            className="mt-3 pt-3 border-t border-terminal-border"
          >
            <p className="text-xs text-terminal-muted mb-2">
              {mt5Status.reason ?? "Make sure MT5 terminal is running and logged into your Exness demo account."}
            </p>
            <Button size="sm" variant="outline" className="w-full" onClick={connectMT5}>
              Retry MT5 Connection
            </Button>
          </motion.div>
        )}
      </CardContent>
    </Card>
  );
}
