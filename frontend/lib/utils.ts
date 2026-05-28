import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPrice(price: number, decimals = 5): string {
  if (!price) return "-.-----";
  return price.toFixed(decimals);
}

export function formatCurrency(amount: number, decimals = 2): string {
  const abs = Math.abs(amount);
  const formatted = abs.toLocaleString("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
  return amount < 0 ? `-$${formatted}` : `$${formatted}`;
}

export function formatPnL(pnl: number): string {
  const prefix = pnl >= 0 ? "+" : "";
  return `${prefix}${formatCurrency(pnl)}`;
}

export function formatPercent(value: number, decimals = 2): string {
  const prefix = value >= 0 ? "+" : "";
  return `${prefix}${value.toFixed(decimals)}%`;
}

export function formatPips(pips: number): string {
  const prefix = pips >= 0 ? "+" : "";
  return `${prefix}${pips.toFixed(1)} pips`;
}

export function getPnlClass(value: number): string {
  if (value > 0) return "text-terminal-bull";
  if (value < 0) return "text-terminal-bear";
  return "text-terminal-muted";
}

export function getBiasColor(bias: string): string {
  switch (bias?.toLowerCase()) {
    case "bullish": return "text-terminal-bull";
    case "bearish": return "text-terminal-bear";
    default: return "text-terminal-warning";
  }
}

export function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.7) return "text-terminal-bull";
  if (confidence >= 0.5) return "text-terminal-warning";
  return "text-terminal-bear";
}

export function formatTime(date: Date | string): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });
}

export function formatDate(date: Date | string): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return d.toLocaleDateString("en-US", { month: "short", day: "2-digit", year: "numeric" });
}

export function getSession(): string {
  const hour = new Date().getUTCHours();
  if (hour >= 22 || hour < 8) return "Asian";
  if (hour >= 8 && hour < 12) return "London";
  if (hour >= 12 && hour < 16) return "NY/London";
  if (hour >= 16 && hour < 22) return "New York";
  return "Closed";
}

export function getSessionColor(session: string): string {
  switch (session) {
    case "London": return "text-terminal-accent";
    case "NY/London": return "text-terminal-bull";
    case "New York": return "text-terminal-warning";
    case "Asian": return "text-purple-400";
    default: return "text-terminal-muted";
  }
}
