import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "AI Trading Companion",
  description: "Professional AI-powered trading terminal",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-terminal-bg text-terminal-text antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
