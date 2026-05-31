"use client";

import { useEffect, useRef } from "react";
import { useMT5Store } from "@/store";
import type { AccountInfo, MT5Position } from "@/types";

const WS_URL = `${(process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000")}/ws/mt5`;

export function useMT5Socket() {
  const { setAccount, setPositions, setStatus } = useMT5Store();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;

    function connect() {
      if (!mountedRef.current) return;

      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        if (!mountedRef.current) return;
        try {
          const payload = JSON.parse(event.data) as {
            account: AccountInfo | null;
            positions: MT5Position[];
          };
          if (payload.account) {
            setAccount(payload.account);
            // Sync connected status so AccountPanel shows data
            setStatus({ connected: true });
          }
          if (payload.positions) setPositions(payload.positions);
        } catch { /* ignore */ }
      };

      ws.onclose = () => {
        if (mountedRef.current) {
          reconnectRef.current = setTimeout(connect, 4000);
        }
      };

      ws.onerror = () => ws.close();
    }

    connect();

    return () => {
      mountedRef.current = false;
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      wsRef.current?.close();
    };
  }, [setAccount, setPositions, setStatus]);
}
