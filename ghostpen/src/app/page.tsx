"use client";

import { useState, useCallback } from "react";
import Header from "@/components/layout/Header";
import PlatformStatus from "@/components/status/PlatformStatus";
import TopicForm from "@/components/generate/TopicForm";
import ContentCard from "@/components/generate/ContentCard";
import ImagePreview from "@/components/generate/ImagePreview";
import {
  generateContent,
  generateImagePrompt,
  generateImage,
  postContent,
} from "@/lib/api";
import type { Platform, Tone, GenerateResponse } from "@/types";

export default function Dashboard() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedContent, setGeneratedContent] = useState<Record<string, string>>({});
  const [selectedPlatforms, setSelectedPlatforms] = useState<Platform[]>([]);

  // Image state
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [imagePath, setImagePath] = useState<string | null>(null);
  const [imagePrompt, setImagePrompt] = useState("");
  const [isGeneratingImage, setIsGeneratingImage] = useState(false);

  const [error, setError] = useState("");

  const handleGenerateImage = useCallback(async (prompt: string) => {
    setIsGeneratingImage(true);
    try {
      const imgResult = await generateImage(prompt);
      setImageUrl(imgResult.image_url);
      setImagePath(imgResult.image_path);
    } catch (err) {
      console.error("Image generation failed:", err);
    } finally {
      setIsGeneratingImage(false);
    }
  }, []);

  const handleGenerate = useCallback(
    async (topic: string, platforms: Platform[], tone: Tone, wordCount: number) => {
      setIsGenerating(true);
      setError("");
      setGeneratedContent({});
      setImageUrl(null);
      setImagePath(null);
      setImagePrompt("");
      setSelectedPlatforms(platforms);

      try {
        // Generate each platform separately so cards appear as they finish
        // Order: twitter first (fastest), then instagram, then blog (slowest)
        const ordered = [...platforms].sort((a, b) => {
          const priority: Record<string, number> = { twitter: 0, instagram: 1, blog: 2 };
          return (priority[a] ?? 1) - (priority[b] ?? 1);
        });

        let firstContent = "";
        let firstPlatform = platforms[0];

        for (const p of ordered) {
          try {
            const r = await generateContent(topic, p, tone, wordCount);
            setGeneratedContent((prev) => ({ ...prev, ...r.content }));
            if (!firstContent && r.content[p] && !r.content[p].startsWith("[ERROR")) {
              firstContent = r.content[p];
              firstPlatform = p;
            }
          } catch (err) {
            console.error(`Generation failed for ${p}:`, err);
            setGeneratedContent((prev) => ({ ...prev, [p]: `[ERROR: ${err instanceof Error ? err.message : "Failed"}]` }));
          }
        }

        // Auto-generate image from the first successful content
        if (firstContent) {
          setIsGeneratingImage(true);
          try {
            const promptResult = await generateImagePrompt(firstContent, firstPlatform);
            setImagePrompt(promptResult.image_prompt);

            const imgResult = await generateImage(promptResult.image_prompt);
            setImageUrl(imgResult.image_url);
            setImagePath(imgResult.image_path);
          } catch (err) {
            console.error("Image generation failed:", err);
          } finally {
            setIsGeneratingImage(false);
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Generation failed");
      } finally {
        setIsGenerating(false);
      }
    },
    []
  );

  const handlePost = useCallback(
    async (platform: Platform, content: string) => {
      const options: { title?: string; image_path?: string; image_url?: string } = {};
      if (platform === "instagram" && imagePath) {
        options.image_path = imagePath;
      }
      if (platform === "blog" && imageUrl) {
        options.image_url = imageUrl;
      }
      const result = await postContent(platform, content, options);
      if (!result.success) {
        throw new Error(result.error || "Post failed");
      }
    },
    [imagePath, imageUrl]
  );

  const hasContent = Object.keys(generatedContent).length > 0;

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header />

      <main className="flex-1 max-w-6xl mx-auto w-full px-6 py-8">
        {/* Status Bar */}
        <div className="mb-8">
          <PlatformStatus />
        </div>

        {/* Topic Form */}
        <div className="mb-8">
          <TopicForm onGenerate={handleGenerate} isLoading={isGenerating} />
        </div>

        {/* Error */}
        {error && (
          <div className="mb-6 px-4 py-3 rounded-lg bg-red/10 border border-red/20 text-red text-sm">
            {error}
          </div>
        )}

        {/* Generated Content */}
        {hasContent && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Content Cards */}
            <div className="lg:col-span-2 space-y-4">
              <h2
                className="text-lg font-semibold"
                style={{ fontFamily: "var(--font-playfair)" }}
              >
                Generated Content
              </h2>
              {selectedPlatforms.map((platform) =>
                generatedContent[platform] ? (
                  <ContentCard
                    key={platform}
                    platform={platform}
                    content={generatedContent[platform]}
                    onPost={handlePost}
                    imagePath={imagePath || undefined}
                  />
                ) : null
              )}
            </div>

            {/* Image Preview */}
            <div className="space-y-4">
              <h2
                className="text-lg font-semibold"
                style={{ fontFamily: "var(--font-playfair)" }}
              >
                Image
              </h2>
              <ImagePreview
                imageUrl={imageUrl}
                imagePrompt={imagePrompt}
                isGenerating={isGeneratingImage}
                onRegenerate={handleGenerateImage}
              />
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-border px-6 py-4 bg-foreground text-background">
        <div className="max-w-6xl mx-auto flex items-center justify-between text-xs text-background/60">
          <span>GhostPen - AI writes, you own it</span>
          <span>Powered by GPT-OSS 120B</span>
        </div>
      </footer>
    </div>
  );
}
