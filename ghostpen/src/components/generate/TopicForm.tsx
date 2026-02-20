"use client";

import { useState } from "react";
import { Sparkles, BookOpen, Twitter, Instagram, Loader2 } from "lucide-react";
import type { Platform, Tone } from "@/types";

interface TopicFormProps {
  onGenerate: (topic: string, platforms: Platform[], tone: Tone, wordCount: number) => void;
  isLoading: boolean;
}

const TONES: { value: Tone; label: string }[] = [
  { value: "casual", label: "Casual" },
  { value: "reflective", label: "Reflective" },
  { value: "technical", label: "Technical" },
  { value: "humorous", label: "Humorous" },
];

const PLATFORMS: { value: Platform; label: string; icon: React.ReactNode }[] = [
  { value: "blog", label: "Blog", icon: <BookOpen className="w-4 h-4" /> },
  { value: "twitter", label: "X / Twitter", icon: <Twitter className="w-4 h-4" /> },
  { value: "instagram", label: "Instagram", icon: <Instagram className="w-4 h-4" /> },
];

export default function TopicForm({ onGenerate, isLoading }: TopicFormProps) {
  const [topic, setTopic] = useState("");
  const [selectedPlatforms, setSelectedPlatforms] = useState<Platform[]>(["blog", "twitter", "instagram"]);
  const [tone, setTone] = useState<Tone>("casual");
  const [wordCount, setWordCount] = useState(500);

  const togglePlatform = (p: Platform) => {
    setSelectedPlatforms((prev) =>
      prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p]
    );
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim() || selectedPlatforms.length === 0) return;
    onGenerate(topic, selectedPlatforms, tone, wordCount);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Topic Input */}
      <div>
        <label className="block text-sm font-medium text-muted mb-2">Topic</label>
        <textarea
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="What do you want to write about?"
          className="w-full bg-surface border border-border rounded-lg px-4 py-3 text-foreground placeholder-muted/50 focus:outline-none focus:border-gold/50 focus:ring-1 focus:ring-gold/20 transition-colors min-h-[80px]"
          rows={2}
        />
      </div>

      {/* Platform Selection */}
      <div>
        <label className="block text-sm font-medium text-muted mb-2">Platforms</label>
        <div className="flex gap-2">
          {PLATFORMS.map((p) => (
            <button
              key={p.value}
              type="button"
              onClick={() => togglePlatform(p.value)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg border text-sm transition-all ${
                selectedPlatforms.includes(p.value)
                  ? "bg-gold/10 border-gold/30 text-gold"
                  : "bg-surface border-border text-muted hover:border-border hover:bg-surface-hover"
              }`}
            >
              {p.icon}
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tone & Word Count */}
      <div className="flex gap-4">
        <div className="flex-1">
          <label className="block text-sm font-medium text-muted mb-2">Tone</label>
          <select
            value={tone}
            onChange={(e) => setTone(e.target.value as Tone)}
            className="w-full bg-surface border border-border rounded-lg px-4 py-2.5 text-foreground focus:outline-none focus:border-gold/50 transition-colors"
          >
            {TONES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </div>

        {selectedPlatforms.includes("blog") && (
          <div className="flex-1">
            <label className="block text-sm font-medium text-muted mb-2">
              Word Count: {wordCount}
            </label>
            <input
              type="range"
              min={200}
              max={2000}
              step={100}
              value={wordCount}
              onChange={(e) => setWordCount(Number(e.target.value))}
              className="w-full mt-2 accent-gold"
            />
            <div className="flex justify-between text-xs text-muted mt-1">
              <span>200</span>
              <span>2000</span>
            </div>
          </div>
        )}
      </div>

      {/* Generate Button */}
      <button
        type="submit"
        disabled={isLoading || !topic.trim() || selectedPlatforms.length === 0}
        className="w-full flex items-center justify-center gap-2 bg-gold hover:bg-gold-dim text-background font-semibold py-3 px-6 rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {isLoading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Generating...
          </>
        ) : (
          <>
            <Sparkles className="w-5 h-5" />
            Generate Content
          </>
        )}
      </button>
    </form>
  );
}
