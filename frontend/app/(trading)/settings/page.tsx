"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ConnectionStatus } from "@/components/status/ConnectionStatus";
import { Settings } from "lucide-react";
import { systemApi } from "@/services/api";

export default function SettingsPage() {
  const { data: status } = useQuery({
    queryKey: ["system-status"],
    queryFn: () => systemApi.status().then((r) => r.data),
    refetchInterval: 15_000,
  });

  return (
    <div className="space-y-4 animate-slide-up max-w-2xl">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="w-4 h-4 text-terminal-accent" />
            System Settings
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <ConnectionStatus />

          {status && (
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="bg-terminal-secondary rounded-md p-3">
                <p className="text-terminal-muted text-xs mb-1">Version</p>
                <p className="font-mono">{status.version}</p>
              </div>
              <div className="bg-terminal-secondary rounded-md p-3">
                <p className="text-terminal-muted text-xs mb-1">Trading Mode</p>
                <p className="font-mono capitalize">{status.trading_mode}</p>
              </div>
            </div>
          )}

          <p className="text-terminal-muted text-xs text-center pt-2">
            Full settings panel coming in Phase 3.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
