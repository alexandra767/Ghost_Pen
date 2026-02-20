"use client";

import { useState } from "react";
import { ImageIcon, RefreshCw, Loader2, Edit3 } from "lucide-react";
import { getImageUrl } from "@/lib/api";

interface ImagePreviewProps {
  imageUrl: string | null;
  imagePrompt: string;
  isGenerating: boolean;
  onRegenerate: (prompt: string) => void;
}

export default function ImagePreview({
  imageUrl,
  imagePrompt,
  isGenerating,
  onRegenerate,
}: ImagePreviewProps) {
  const [editingPrompt, setEditingPrompt] = useState(false);
  const [editedPrompt, setEditedPrompt] = useState(imagePrompt);

  // Sync prompt when it changes externally
  if (imagePrompt !== editedPrompt && !editingPrompt) {
    setEditedPrompt(imagePrompt);
  }

  return (
    <div className="bg-surface border border-border rounded-xl overflow-hidden shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div className="flex items-center gap-2 text-terracotta">
          <ImageIcon className="w-4 h-4" />
          <span className="font-medium text-sm">Generated Image</span>
        </div>
      </div>

      {/* Image */}
      <div className="p-4">
        {isGenerating ? (
          <div className="flex flex-col items-center justify-center py-16 text-muted gap-3">
            <Loader2 className="w-8 h-8 animate-spin text-terracotta" />
            <span className="text-sm">Generating image from your content...</span>
          </div>
        ) : imageUrl ? (
          <div className="relative">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={getImageUrl(imageUrl)}
              alt="Generated content image"
              className="w-full rounded-lg"
            />
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-16 text-muted gap-2">
            <ImageIcon className="w-8 h-8" />
            <span className="text-sm">Image will generate after content</span>
          </div>
        )}
      </div>

      {/* Prompt */}
      {imagePrompt && (
        <div className="px-4 pb-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs text-muted">Image prompt</span>
            <button
              onClick={() => setEditingPrompt(!editingPrompt)}
              className="text-xs text-muted hover:text-foreground transition-colors"
            >
              <Edit3 className="w-3 h-3" />
            </button>
          </div>
          {editingPrompt ? (
            <textarea
              value={editedPrompt}
              onChange={(e) => setEditedPrompt(e.target.value)}
              className="w-full bg-background border border-border rounded-lg px-3 py-2 text-xs text-foreground/70 focus:outline-none focus:border-terracotta/50 min-h-[60px]"
            />
          ) : (
            <p className="text-xs text-muted leading-relaxed">{imagePrompt}</p>
          )}

          <button
            onClick={() => onRegenerate(editedPrompt)}
            disabled={isGenerating}
            className="flex items-center gap-1.5 mt-3 px-3 py-1.5 rounded-full text-xs bg-terracotta/10 text-terracotta hover:bg-terracotta/20 transition-colors disabled:opacity-40"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Regenerate Image
          </button>
        </div>
      )}
    </div>
  );
}
