"use client";

import { useEffect, useRef } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { useAppStore, useMT5Store } from "@/store";
import { systemApi, mt5Api } from "@/services/api";
import { useMT5Socket } from "@/hooks/useMT5Socket";
import { usePriceSocket } from "@/hooks/usePriceSocket";

const PRICE_SYMBOLS  = ["XAUUSD", "EURUSD", "GBPUSD", "BTCUSDT", "US100"];
const STATUS_INTERVAL = 15_000;

export default function TradingLayout({ children }: { children: React.ReactNode }) {
  const { setSystemStatus } = useAppStore();
  const { setStatus } = useMT5Store();
  const mountedRef = useRef(true);

  // ── Real-time WebSocket feeds ──────────────────────────────────────────────
  useMT5Socket();
  usePriceSocket(PRICE_SYMBOLS);

  useEffect(() => {
    mountedRef.current = true;

    async function fetchStatus() {
      try {
        const [statusRes, mt5StatusRes] = await Promise.allSettled([
          systemApi.status(),
          mt5Api.status(),
        ]);
        if (!mountedRef.current) return;
        if (statusRes.status === "fulfilled") setSystemStatus(statusRes.value.data);
        if (mt5StatusRes.status === "fulfilled") setStatus(mt5StatusRes.value.data);
      } catch { /* swallow */ }
    }

    fetchStatus();
    const timer = setInterval(fetchStatus, STATUS_INTERVAL);

    return () => {
      mountedRef.current = false;
      clearInterval(timer);
    };
  }, [setSystemStatus, setStatus]);

  return (
    <div className="flex h-screen overflow-hidden bg-terminal-bg">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header />
        <main className="flex-1 overflow-auto p-4">
          {children}
        </main>
      </div>
    </div>
  );
}
