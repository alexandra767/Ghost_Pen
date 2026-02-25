"use client";

import { useEffect, useState } from "react";
import { getHealth, getModelStatus, startModel, stopModel } from "@/lib/api";
import type { HealthResponse } from "@/types";
import { Activity, BookOpen, Twitter, Instagram, ImageIcon, Power, Loader2 } from "lucide-react";

export default function PlatformStatus() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState(false);
  const [modelLoaded, setModelLoaded] = useState(false);
  const [modelAction, setModelAction] = useState(false);

  const checkHealth = async () => {
    try {
      const data = await getHealth();
      setHealth(data);
      setError(false);
      setModelLoaded(data.model_server === "ok");
    } catch {
      setError(true);
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleModelToggle = async () => {
    setModelAction(true);
    try {
      if (modelLoaded) {
        await stopModel();
        setModelLoaded(false);
      } else {
        await startModel();
        setModelLoaded(true);
      }
      // Refresh health after toggle
      setTimeout(checkHealth, 2000);
    } catch {
      // ignore
    } finally {
      setModelAction(false);
    }
  };

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
        <div className={`w-2 h-2 rounded-full ${modelLoaded ? "bg-sage" : "bg-red"}`} />
        <span>Model</span>
        <button
          onClick={handleModelToggle}
          disabled={modelAction}
          title={modelLoaded ? "Unload model (free GPU)" : "Load model"}
          className={`ml-1 p-1 rounded transition-colors ${
            modelLoaded
              ? "text-sage hover:text-red hover:bg-red/10"
              : "text-red hover:text-sage hover:bg-sage/10"
          } disabled:opacity-40`}
        >
          {modelAction ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Power className="w-3.5 h-3.5" />
          )}
        </button>
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
