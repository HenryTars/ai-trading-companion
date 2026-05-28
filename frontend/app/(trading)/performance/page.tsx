"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity } from "lucide-react";

export default function PerformancePage() {
  return (
    <div className="space-y-4 animate-slide-up">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-terminal-accent" />
            Performance Analytics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-terminal-muted text-sm">Performance analytics coming in Phase 3.</p>
        </CardContent>
      </Card>
    </div>
  );
}
