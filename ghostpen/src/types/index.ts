export interface GenerateRequest {
  topic: string;
  platform: "all" | "blog" | "twitter" | "instagram";
  tone: string;
  word_count: number;
  image_description?: string;
  auto_post: boolean;
  image_path?: string;
}

export interface GenerateResponse {
  content: Record<string, string>;
  posted: Record<string, PostResult>;
}

export interface PostResult {
  success: boolean;
  platform?: string;
  post_id?: string;
  url?: string;
  error?: string;
}

export interface PlatformStatus {
  configured: boolean;
  valid: boolean;
  error?: string;
}

export interface HealthResponse {
  status: string;
  model_server: string;
  platforms: string[];
  image_generation: boolean;
}

export interface ImagePromptResponse {
  image_prompt: string;
}

export interface ImageGenerateResponse {
  image_path: string;
  image_url: string;
  filename: string;
}

export type Platform = "blog" | "twitter" | "instagram";

export type Tone = "casual" | "reflective" | "technical" | "humorous";
