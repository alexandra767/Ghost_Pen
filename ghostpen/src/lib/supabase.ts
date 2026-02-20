import { createClient, SupabaseClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";

let supabase: SupabaseClient | null = null;

function getClient(): SupabaseClient | null {
  if (!supabaseUrl || !supabaseAnonKey) return null;
  if (!supabase) {
    supabase = createClient(supabaseUrl, supabaseAnonKey);
  }
  return supabase;
}

export interface BlogPostRow {
  id: string;
  title: string;
  slug: string;
  content: string;
  excerpt: string | null;
  tags: string[];
  status: string;
  image_url: string | null;
  published_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface BlogPost {
  id: string;
  title: string;
  slug: string;
  content: string;
  excerpt: string;
  tags: string[];
  imageUrl: string | null;
  publishedAt: string;
  createdAt: string;
  readTime: string;
}

function estimateReadTime(content: string): string {
  const words = content.split(/\s+/).length;
  const minutes = Math.max(1, Math.ceil(words / 200));
  return `${minutes} min read`;
}

function mapPost(row: BlogPostRow): BlogPost {
  return {
    id: row.id,
    title: row.title,
    slug: row.slug,
    content: row.content,
    excerpt: row.excerpt || "",
    tags: row.tags || [],
    imageUrl: row.image_url || null,
    publishedAt: row.published_at || row.created_at,
    createdAt: row.created_at,
    readTime: estimateReadTime(row.content),
  };
}

export async function getBlogPosts(): Promise<BlogPost[]> {
  const client = getClient();
  if (!client) return [];

  const { data, error } = await client
    .from("blog_posts")
    .select("*")
    .eq("status", "published")
    .order("published_at", { ascending: false });

  if (error) {
    console.error("Error fetching blog posts:", error);
    return [];
  }

  return (data ?? []).map(mapPost);
}

export async function getBlogPostBySlug(slug: string): Promise<BlogPost | null> {
  const client = getClient();
  if (!client) return null;

  const { data, error } = await client
    .from("blog_posts")
    .select("*")
    .eq("slug", slug)
    .eq("status", "published")
    .single();

  if (error || !data) return null;
  return mapPost(data);
}

export async function getBlogPostSlugs(): Promise<string[]> {
  const client = getClient();
  if (!client) return [];

  const { data, error } = await client
    .from("blog_posts")
    .select("slug")
    .eq("status", "published");

  if (error) return [];
  return (data ?? []).map((d) => d.slug);
}
