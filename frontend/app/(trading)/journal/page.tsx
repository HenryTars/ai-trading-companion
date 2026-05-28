"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BookOpen } from "lucide-react";

export default function JournalPage() {
  return (
    <div className="space-y-4 animate-slide-up">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-terminal-accent" />
            Trade Journal
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-terminal-muted text-sm">Journal UI coming in Phase 3.</p>
        </CardContent>
      </Card>
    </div>
  );
}
