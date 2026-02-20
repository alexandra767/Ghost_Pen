"use client";

import { useEffect, useState } from "react";
import { getHealth } from "@/lib/api";
import type { HealthResponse } from "@/types";
import { Activity, BookOpen, Twitter, Instagram, ImageIcon } from "lucide-react";

export default function PlatformStatus() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    const check = async () => {
      try {
        const data = await getHealth();
        setHealth(data);
        setError(false);
      } catch {
        setError(true);
      }
    };
    check();
    const interval = setInterval(check, 30000);
    return () => clearInterval(interval);
  }, []);

  if (error) {
    return (
      <div className="flex items-center gap-2 text-sm text-red">
        <Activity className="w-4 h-4" />
        <span>Backend offline</span>
      </div>
    );
  }

  if (!health) return null;

  const platformIcons: Record<string, React.ReactNode> = {
    blog: <BookOpen className="w-3.5 h-3.5" />,
    twitter: <Twitter className="w-3.5 h-3.5" />,
    instagram: <Instagram className="w-3.5 h-3.5" />,
  };

  return (
    <div className="flex items-center gap-4 text-xs text-muted">
      <div className="flex items-center gap-1.5">
        <div className={`w-2 h-2 rounded-full ${health.model_server === "ok" ? "bg-sage" : "bg-red"}`} />
        <span>Model</span>
      </div>
      {["blog", "twitter", "instagram"].map((p) => (
        <div key={p} className="flex items-center gap-1.5">
          <div className={`w-2 h-2 rounded-full ${health.platforms.includes(p) ? "bg-sage" : "bg-border"}`} />
          {platformIcons[p]}
          <span className="capitalize">{p === "twitter" ? "X" : p}</span>
        </div>
      ))}
      <div className="flex items-center gap-1.5">
        <div className={`w-2 h-2 rounded-full ${health.image_generation ? "bg-sage" : "bg-border"}`} />
        <ImageIcon className="w-3.5 h-3.5" />
        <span>Images</span>
      </div>
    </div>
  );
}
