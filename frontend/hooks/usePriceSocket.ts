"use client";

import { useEffect, useRef } from "react";
import { usePriceStore } from "@/store";
import type { PriceTick } from "@/types";

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";

export function usePriceSocket(symbols: string[]) {
  const { setTick } = usePriceStore();
  const socketsRef = useRef<Map<string, WebSocket>>(new Map());
  const mountedRef = useRef(true);
  const timersRef  = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  useEffect(() => {
    mountedRef.current = true;

    function connect(symbol: string) {
      if (!mountedRef.current) return;

      const ws = new WebSocket(`${WS_BASE}/ws/price/${symbol}`);
      socketsRef.current.set(symbol, ws);

      ws.onmessage = (event) => {
        if (!mountedRef.current) return;
        try {
          const tick = JSON.parse(event.data) as PriceTick;
          setTick(tick);
        } catch { /* ignore */ }
      };

      ws.onclose = () => {
        if (mountedRef.current) {
          const t = setTimeout(() => connect(symbol), 4000);
          timersRef.current.set(symbol, t);
        }
      };

      ws.onerror = () => ws.close();
    }

    symbols.forEach(connect);

    return () => {
      mountedRef.current = false;
      timersRef.current.forEach((t) => clearTimeout(t));
      socketsRef.current.forEach((ws) => ws.close());
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbols.join(","), setTick]);
}
