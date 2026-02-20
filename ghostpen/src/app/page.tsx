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
        // Generate content for all selected platforms
        let result: GenerateResponse;

        if (platforms.length === 3) {
          result = await generateContent(topic, "all", tone, wordCount);
        } else {
          // Generate one at a time for partial selection
          const content: Record<string, string> = {};
          for (const p of platforms) {
            const r = await generateContent(topic, p, tone, wordCount);
            Object.assign(content, r.content);
          }
          result = { content, posted: {} };
        }

        setGeneratedContent(result.content);

        // Auto-generate image from the first available content
        const firstContent = result.content[platforms[0]] || Object.values(result.content)[0];
        if (firstContent && !firstContent.startsWith("[ERROR")) {
          setIsGeneratingImage(true);
          try {
            const promptResult = await generateImagePrompt(firstContent, platforms[0]);
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
    <div className="min-h-screen flex flex-col">
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
              <h2 className="text-lg font-semibold" style={{ fontFamily: "var(--font-space)" }}>
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
              <h2 className="text-lg font-semibold" style={{ fontFamily: "var(--font-space)" }}>
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
      <footer className="border-t border-border px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between text-xs text-muted">
          <span>GhostPen - AI writes, you own it</span>
          <span>Powered by GPT-OSS 120B</span>
        </div>
      </footer>
    </div>
  );
}
