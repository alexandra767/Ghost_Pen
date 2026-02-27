"use client";

import { useState } from "react";
import { Sparkles, BookOpen, Twitter, Instagram, Loader2, MapPin } from "lucide-react";
import type { Platform, Tone } from "@/types";

interface TopicFormProps {
  onGenerate: (topic: string, platforms: Platform[], tone: Tone, wordCount: number, isWanderlink: boolean) => void;
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

const WANDERLINK_TOPICS = [
  "How WanderLink's AI helps you find hidden gems most tourists miss",
  "Why I built an emergency SOS feature into a travel app (and made it free)",
  "Planning your next trip in 5 minutes with AI-powered itineraries",
  "The end of 20 open browser tabs: how one app replaced my entire travel toolkit",
  "Meeting fellow travelers safely with WanderLink's Nearby feature",
  "Budget travel made easy: splitting bills and tracking expenses on the go",
  "From solo founder to App Store: the story behind WanderLink",
  "5 hidden gem destinations WanderLink's AI recommends for spring travel",
  "Why every solo traveler needs a safety-first travel companion app",
  "WanderLink's Daily Digest: your personal AI travel concierge",
  "Walking tours, local food, and off-the-beaten-path adventures with WanderLink",
  "WanderLink's new iOS widgets: your trip countdown right on your home screen",
  "How WanderLink works in 150+ countries — even without internet",
  "Track your travel stats: WanderLink's new analytics dashboard",
  "Android is coming: the WanderLink expansion story",
  "QR code payment splits: the easiest way to split travel expenses",
  "WanderLink's redesigned Discovery tab: find events, tours, and weather in one tap",
  "WanderLink full feature showcase: every tool in one travel app",
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
    onGenerate(topic, selectedPlatforms, tone, wordCount, isWanderlinkTopic);
  };

  const [showWanderLink, setShowWanderLink] = useState(false);
  const [isWanderlinkTopic, setIsWanderlinkTopic] = useState(false);

  return (
    <form onSubmit={handleSubmit} className="bg-surface rounded-xl shadow-sm border border-border p-6 space-y-5">
      {/* Topic Input */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-sm font-medium text-muted">Topic</label>
          <button
            type="button"
            onClick={() => setShowWanderLink(!showWanderLink)}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium transition-all ${
              showWanderLink
                ? "bg-blue-500 text-white"
                : "bg-blue-500/10 text-blue-400 hover:bg-blue-500/20"
            }`}
          >
            <MapPin className="w-3 h-3" />
            WanderLink Topics
          </button>
        </div>
        <textarea
          value={topic}
          onChange={(e) => { setTopic(e.target.value); setIsWanderlinkTopic(false); }}
          placeholder="What do you want to write about?"
          className="w-full bg-background border border-border rounded-lg px-4 py-3 text-foreground placeholder-muted/50 focus:outline-none focus:border-terracotta/50 focus:ring-1 focus:ring-terracotta/20 transition-colors min-h-[80px]"
          rows={2}
        />
      </div>

      {/* WanderLink Quick Topics */}
      {showWanderLink && (
        <div className="bg-blue-950 border border-blue-500/30 rounded-lg p-4">
          <p className="text-sm font-medium text-white mb-3">Click a topic to use it:</p>
          <div className="flex flex-wrap gap-2">
            {WANDERLINK_TOPICS.map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => {
                  setTopic(t);
                  setIsWanderlinkTopic(true);
                  setShowWanderLink(false);
                }}
                className="text-sm px-3 py-2 rounded-full bg-blue-600/30 text-white hover:bg-blue-500/50 transition-colors text-left"
              >
                {t}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Platform Selection */}
      <div>
        <label className="block text-sm font-medium text-muted mb-2">Platforms</label>
        <div className="flex gap-2">
          {PLATFORMS.map((p) => (
            <button
              key={p.value}
              type="button"
              onClick={() => togglePlatform(p.value)}
              className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm transition-all ${
                selectedPlatforms.includes(p.value)
                  ? "bg-terracotta text-white ring-2 ring-terracotta/30"
                  : "bg-secondary border border-border text-muted hover:bg-surface-hover"
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
            className="w-full bg-background border border-border rounded-lg px-4 py-2.5 text-foreground focus:outline-none focus:border-terracotta/50 transition-colors"
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
              className="w-full mt-2 accent-terracotta"
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
        className="w-full flex items-center justify-center gap-2 bg-terracotta hover:bg-terracotta-dark text-white font-semibold py-3 px-6 rounded-full transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
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
