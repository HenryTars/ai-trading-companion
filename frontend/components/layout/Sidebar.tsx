"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { useAppStore, useMT5Store } from "@/store";
import {
  LayoutDashboard,
  LineChart,
  BookOpen,
  Bot,
  Settings,
  Activity,
  Layers,
  ChevronLeft,
  ChevronRight,
  Zap,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { formatCurrency } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/dashboard",  icon: LayoutDashboard, label: "Dashboard" },
  { href: "/chart",      icon: LineChart,        label: "Chart Analysis" },
  { href: "/patterns",   icon: Layers,           label: "Pattern Lab" },
  { href: "/journal",    icon: BookOpen,         label: "Trade Journal" },
  { href: "/performance",icon: Activity,         label: "Performance" },
  { href: "/autonomous", icon: Bot,              label: "Autonomous" },
  { href: "/settings",   icon: Settings,         label: "Settings" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarCollapsed, setSidebarCollapsed } = useAppStore();
  const { status: mt5Status, account } = useMT5Store();

  return (
    <motion.aside
      animate={{ width: sidebarCollapsed ? 56 : 220 }}
      transition={{ duration: 0.2, ease: "easeInOut" }}
      className="relative flex flex-col h-full bg-terminal-card border-r border-terminal-border overflow-hidden shrink-0"
    >
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-3 py-4 border-b border-terminal-border h-14">
        <div className="w-8 h-8 rounded-lg bg-terminal-accent/20 border border-terminal-accent/30 flex items-center justify-center shrink-0">
          <Zap className="w-4 h-4 text-terminal-accent" />
        </div>
        <AnimatePresence>
          {!sidebarCollapsed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
              className="overflow-hidden whitespace-nowrap"
            >
              <p className="text-sm font-bold text-terminal-text leading-tight">AI Trader</p>
              <p className="text-[10px] text-terminal-muted">v2.0 · Demo</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Nav items */}
      <nav className="flex-1 py-3 space-y-0.5 px-1.5 overflow-y-auto">
        {NAV_ITEMS.map(({ href, icon: Icon, label }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-2.5 py-2 rounded-md text-sm transition-colors group",
                active
                  ? "bg-terminal-accent/15 text-terminal-accent border border-terminal-accent/20"
                  : "text-terminal-text-secondary hover:bg-terminal-hover hover:text-terminal-text"
              )}
            >
              <Icon className={cn("w-4 h-4 shrink-0", active && "text-terminal-accent")} />
              <AnimatePresence>
                {!sidebarCollapsed && (
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.15 }}
                    className="whitespace-nowrap overflow-hidden"
                  >
                    {label}
                  </motion.span>
                )}
              </AnimatePresence>
            </Link>
          );
        })}
      </nav>

      {/* Account + Status */}
      <div className="border-t border-terminal-border px-2 py-3 space-y-2">
        {/* MT5 connection status */}
        <div
          className={cn(
            "flex items-center gap-2 px-2 py-1.5 rounded-md text-xs",
            mt5Status.connected ? "text-terminal-bull" : "text-terminal-bear"
          )}
        >
          <span
            className={cn(
              "w-2 h-2 rounded-full shrink-0 pulse-dot",
              mt5Status.connected ? "bg-terminal-bull" : "bg-terminal-bear"
            )}
          />
          <AnimatePresence>
            {!sidebarCollapsed && (
              <motion.span
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                className="whitespace-nowrap"
              >
                MT5 {mt5Status.connected ? "Connected" : "Disconnected"}
              </motion.span>
            )}
          </AnimatePresence>
        </div>

        {/* Balance */}
        {account && !sidebarCollapsed && (
          <div className="px-2 py-1.5 bg-terminal-secondary rounded-md">
            <p className="text-[10px] text-terminal-muted uppercase tracking-wider">Balance</p>
            <p className="text-sm font-mono font-semibold text-terminal-text">
              {formatCurrency(account.balance)}
            </p>
          </div>
        )}
      </div>

      {/* Collapse toggle */}
      <button
        onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
        className="absolute top-4 -right-3 w-6 h-6 rounded-full bg-terminal-card border border-terminal-border flex items-center justify-center hover:bg-terminal-hover transition-colors z-10"
      >
        {sidebarCollapsed
          ? <ChevronRight className="w-3 h-3 text-terminal-muted" />
          : <ChevronLeft className="w-3 h-3 text-terminal-muted" />}
      </button>
    </motion.aside>
  );
}
