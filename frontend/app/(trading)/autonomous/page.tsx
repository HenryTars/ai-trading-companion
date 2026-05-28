"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Bot } from "lucide-react";

export default function AutonomousPage() {
  return (
    <div className="space-y-4 animate-slide-up">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bot className="w-4 h-4 text-terminal-accent" />
            Autonomous Trading Engine
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-terminal-muted text-sm">Autonomous trading control panel coming in Phase 4.</p>
        </CardContent>
      </Card>
    </div>
  );
}
