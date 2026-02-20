import type {
  GenerateResponse,
  PlatformStatus,
  HealthResponse,
  ImagePromptResponse,
  ImageGenerateResponse,
  PostResult,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const error = await res.text();
    throw new Error(error || `API error: ${res.status}`);
  }
  return res.json();
}

export async function generateContent(
  topic: string,
  platform: string,
  tone: string,
  wordCount: number
): Promise<GenerateResponse> {
  return apiFetch<GenerateResponse>("/generate", {
    method: "POST",
    body: JSON.stringify({
      topic,
      platform,
      tone,
      word_count: wordCount,
      auto_post: false,
    }),
  });
}

export async function generateImagePrompt(
  content: string,
  platform: string
): Promise<ImagePromptResponse> {
  return apiFetch<ImagePromptResponse>("/generate-image-prompt", {
    method: "POST",
    body: JSON.stringify({ content, platform }),
  });
}

export async function generateImage(
  prompt: string
): Promise<ImageGenerateResponse> {
  return apiFetch<ImageGenerateResponse>("/generate-image", {
    method: "POST",
    body: JSON.stringify({ prompt }),
  });
}

export async function postContent(
  platform: string,
  content: string,
  options?: { title?: string; image_path?: string; image_url?: string; tags?: string[] }
): Promise<PostResult> {
  return apiFetch<PostResult>(`/post/${platform}`, {
    method: "POST",
    body: JSON.stringify({ content, ...options }),
  });
}

export async function getPlatforms(): Promise<Record<string, PlatformStatus>> {
  return apiFetch<Record<string, PlatformStatus>>("/platforms");
}

export async function getHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/health");
}

export function getImageUrl(imageUrl: string): string {
  return `${API_BASE}${imageUrl}`;
}

// === Blog API ===

export interface BlogPostAPI {
  id: string;
  title: string;
  slug: string;
  content: string;
  excerpt: string;
  tags: string[];
  image_url: string | null;
  status: string;
  published_at: string | null;
  created_at: string;
  updated_at: string;
}

export async function getBlogPostsAPI(): Promise<BlogPostAPI[]> {
  return apiFetch<BlogPostAPI[]>("/api/blog/posts");
}

export async function getBlogPostBySlugAPI(slug: string): Promise<BlogPostAPI> {
  return apiFetch<BlogPostAPI>(`/api/blog/posts/${slug}`);
}

export async function deleteBlogPost(postId: string): Promise<{ success: boolean }> {
  return apiFetch<{ success: boolean }>(`/api/blog/posts/${postId}`, {
    method: "DELETE",
  });
}
