"use client";

import { useState } from "react";
import { BookOpen, Twitter, Instagram, Copy, Check, Send, Loader2, Edit3 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import type { Platform } from "@/types";

interface ContentCardProps {
  platform: Platform;
  content: string;
  onPost: (platform: Platform, content: string) => Promise<void>;
  imagePath?: string;
}

const PLATFORM_CONFIG: Record<Platform, { icon: React.ReactNode; label: string; maxLen?: number }> = {
  blog: { icon: <BookOpen className="w-4 h-4" />, label: "Blog" },
  twitter: { icon: <Twitter className="w-4 h-4" />, label: "X / Twitter", maxLen: 280 },
  instagram: { icon: <Instagram className="w-4 h-4" />, label: "Instagram", maxLen: 2200 },
};

function linkifyText(text: string) {
  const splitRegex = /(https?:\/\/[^\s]+)/g;
  const parts = text.split(splitRegex);
  return parts.map((part, i) => {
    if (/^https?:\/\//.test(part)) {
      return (
        <a key={i} href={part} target="_blank" rel="noopener noreferrer" className="text-blue-400 underline hover:text-blue-300 break-all">
          {part}
        </a>
      );
    }
    return <span key={i}>{part}</span>;
  });
}

export default function ContentCard({ platform, content, onPost, imagePath }: ContentCardProps) {
  const [copied, setCopied] = useState(false);
  const [posting, setPosting] = useState(false);
  const [posted, setPosted] = useState(false);
  const [postError, setPostError] = useState("");
  const [editing, setEditing] = useState(false);
  const [editedContent, setEditedContent] = useState(content);

  const config = PLATFORM_CONFIG[platform];
  const displayContent = editing ? editedContent : content;
  const charCount = displayContent.length;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(displayContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handlePost = async () => {
    setPosting(true);
    setPostError("");
    try {
      await onPost(platform, displayContent);
      setPosted(true);
    } catch (err) {
      setPostError(err instanceof Error ? err.message : "Post failed");
    } finally {
      setPosting(false);
    }
  };

  return (
    <div className="bg-surface border border-border rounded-xl overflow-hidden shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div className="flex items-center gap-2 text-terracotta">
          {config.icon}
          <span className="font-medium text-sm">{config.label}</span>
        </div>
        <div className="flex items-center gap-2">
          {config.maxLen && (
            <span className={`text-xs ${charCount > config.maxLen ? "text-red" : "text-muted"}`}>
              {charCount}/{config.maxLen}
            </span>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {editing ? (
          <textarea
            value={editedContent}
            onChange={(e) => setEditedContent(e.target.value)}
            className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:border-terracotta/50 min-h-[200px]"
          />
        ) : platform === "blog" ? (
          <div className="prose-ghost text-sm text-foreground/90 max-h-[400px] overflow-y-auto">
            <ReactMarkdown>{displayContent}</ReactMarkdown>
          </div>
        ) : (
          <p className="text-sm text-foreground/90 whitespace-pre-wrap leading-relaxed max-h-[300px] overflow-y-auto">
            {linkifyText(displayContent)}
          </p>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 px-4 py-3 border-t border-border">
        <button
          onClick={() => setEditing(!editing)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs text-muted hover:text-foreground hover:bg-surface-hover transition-colors"
        >
          <Edit3 className="w-3.5 h-3.5" />
          {editing ? "Preview" : "Edit"}
        </button>

        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs text-muted hover:text-foreground hover:bg-surface-hover transition-colors"
        >
          {copied ? <Check className="w-3.5 h-3.5 text-sage" /> : <Copy className="w-3.5 h-3.5" />}
          {copied ? "Copied" : "Copy"}
        </button>

        <div className="flex-1" />

        {postError && <span className="text-xs text-red">{postError}</span>}

        {posted ? (
          <span className="flex items-center gap-1.5 text-xs text-sage">
            <Check className="w-3.5 h-3.5" /> Posted
          </span>
        ) : (
          <button
            onClick={handlePost}
            disabled={posting}
            className="flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs bg-terracotta text-white hover:bg-terracotta-dark transition-colors disabled:opacity-40"
          >
            {posting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
            {posting ? "Posting..." : `Post to ${config.label}`}
          </button>
        )}
      </div>
    </div>
  );
}
