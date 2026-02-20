"use client";

import { PenLine } from "lucide-react";

export default function Header() {
  return (
    <header className="border-b border-border px-6 py-4">
      <div className="max-w-6xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gold/10 flex items-center justify-center">
            <PenLine className="w-5 h-5 text-gold" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight" style={{ fontFamily: "var(--font-space)" }}>
              GhostPen
            </h1>
            <p className="text-xs text-muted">AI content in your voice</p>
          </div>
        </div>
      </div>
    </header>
  );
}
