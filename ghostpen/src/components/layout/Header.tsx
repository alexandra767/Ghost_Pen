"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { PenLine, BookOpen, Sparkles } from "lucide-react";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: Sparkles },
  { href: "/blog", label: "Blog", icon: BookOpen },
];

export default function Header() {
  const pathname = usePathname();

  return (
    <header className="border-b border-border px-6 py-4">
      <div className="max-w-6xl mx-auto flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gold/10 flex items-center justify-center">
            <PenLine className="w-5 h-5 text-gold" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight" style={{ fontFamily: "var(--font-space)" }}>
              GhostPen
            </h1>
            <p className="text-xs text-muted">AI content in your voice</p>
          </div>
        </Link>

        <nav className="flex items-center gap-1">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-colors ${
                  isActive
                    ? "bg-gold/10 text-gold"
                    : "text-muted hover:text-foreground hover:bg-surface-hover"
                }`}
              >
                <Icon className="w-4 h-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
