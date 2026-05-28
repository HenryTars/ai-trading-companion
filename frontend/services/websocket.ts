"use client";

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";

type MessageHandler = (data: unknown) => void;
type StatusHandler = (connected: boolean) => void;

class WebSocketService {
  private sockets = new Map<string, WebSocket>();
  private handlers = new Map<string, Set<MessageHandler>>();
  private statusHandlers = new Map<string, Set<StatusHandler>>();
  private reconnectTimers = new Map<string, ReturnType<typeof setTimeout>>();
  private shouldReconnect = new Map<string, boolean>();

  connect(channel: string, path: string): void {
    if (this.sockets.get(channel)?.readyState === WebSocket.OPEN) return;

    this.shouldReconnect.set(channel, true);
    this._open(channel, path);
  }

  private _open(channel: string, path: string): void {
    const ws = new WebSocket(`${WS_BASE}${path}`);

    ws.onopen = () => {
      this.statusHandlers.get(channel)?.forEach((h) => h(true));
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handlers.get(channel)?.forEach((h) => h(data));
      } catch {
        // ignore malformed frames
      }
    };

    ws.onclose = () => {
      this.statusHandlers.get(channel)?.forEach((h) => h(false));
      if (this.shouldReconnect.get(channel)) {
        const timer = setTimeout(() => this._open(channel, path), 3000);
        this.reconnectTimers.set(channel, timer);
      }
    };

    ws.onerror = () => ws.close();

    this.sockets.set(channel, ws);
  }

  disconnect(channel: string): void {
    this.shouldReconnect.set(channel, false);
    const timer = this.reconnectTimers.get(channel);
    if (timer) clearTimeout(timer);
    this.sockets.get(channel)?.close();
    this.sockets.delete(channel);
  }

  onMessage(channel: string, handler: MessageHandler): () => void {
    if (!this.handlers.has(channel)) this.handlers.set(channel, new Set());
    this.handlers.get(channel)!.add(handler);
    return () => this.handlers.get(channel)?.delete(handler);
  }

  onStatus(channel: string, handler: StatusHandler): () => void {
    if (!this.statusHandlers.has(channel)) this.statusHandlers.set(channel, new Set());
    this.statusHandlers.get(channel)!.add(handler);
    return () => this.statusHandlers.get(channel)?.delete(handler);
  }

  send(channel: string, data: unknown): void {
    const ws = this.sockets.get(channel);
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(data));
    }
  }

  isConnected(channel: string): boolean {
    return this.sockets.get(channel)?.readyState === WebSocket.OPEN;
  }
}

export const wsService = new WebSocketService();

// Pre-defined channels
export const WS_CHANNELS = {
  PRICES: (symbol: string) => `price:${symbol}`,
  MT5_ACCOUNT: "mt5:account",
  MT5_POSITIONS: "mt5:positions",
  SIGNALS: "signals",
} as const;
