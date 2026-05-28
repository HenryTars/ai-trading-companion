"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/services/api";

export interface OHLCVCandle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export function useChartData(symbol: string, timeframe: string) {
  return useQuery<OHLCVCandle[]>({
    queryKey: ["ohlcv", symbol, timeframe],
    queryFn: async () => {
      const res = await api.get<{ candles: OHLCVCandle[] }>(
        `/api/market/ohlcv/${symbol}?timeframe=${timeframe}`
      );
      return res.data.candles;
    },
    staleTime: 60_000,
    refetchInterval: 60_000,
  });
}
