"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Calendar, Clock, ArrowLeft, Tag, Trash2, Loader2 } from "lucide-react";
import { getBlogPostBySlugAPI, getBlogPostsAPI, deleteBlogPost, getImageUrl, type BlogPostAPI } from "@/lib/api";
import { BlogCard } from "@/components/blog/BlogCard";
import Header from "@/components/layout/Header";
import { BlogContent } from "@/components/blog/BlogContent";

export default function BlogDetailPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;

  const [post, setPost] = useState<BlogPostAPI | null>(null);
  const [related, setRelated] = useState<BlogPostAPI[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const [postData, allPosts] = await Promise.all([
          getBlogPostBySlugAPI(slug),
          getBlogPostsAPI(),
        ]);
        setPost(postData);
        setRelated(allPosts.filter((p) => p.slug !== slug).slice(0, 3));
      } catch (err) {
        console.error("Failed to load post:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [slug]);

  const handleDelete = async () => {
    if (!post) return;
    if (!confirm("Are you sure you want to delete this post?")) return;
    setDeleting(true);
    try {
      await deleteBlogPost(post.id);
      router.push("/blog");
    } catch (err) {
      console.error("Failed to delete:", err);
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col bg-background">
        <Header />
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-terracotta" />
        </div>
      </div>
    );
  }

  if (!post) {
    return (
      <div className="min-h-screen flex flex-col bg-background">
        <Header />
        <div className="flex-1 flex flex-col items-center justify-center gap-4">
          <p className="text-muted text-lg">Post not found</p>
          <Link href="/blog" className="text-terracotta hover:underline">Back to Blog</Link>
        </div>
      </div>
    );
  }

  const formattedDate = new Date(post.published_at || post.created_at).toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });

  const wordCount = post.content.split(/\s+/).length;
  const readTime = `${Math.max(1, Math.ceil(wordCount / 200))} min read`;
  const heroImage = post.image_url ? (post.image_url.startsWith("/images/") ? getImageUrl(post.image_url) : post.image_url) : null;

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header />

      {/* Hero */}
      <section className="relative w-full overflow-hidden">
        {heroImage ? (
          <>
            <div className="relative h-[45vh] min-h-[350px] w-full">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={heroImage}
                alt={post.title}
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-[#3C2415]/80 via-[#3C2415]/40 to-transparent" />
            </div>
            <div className="absolute inset-0 flex flex-col justify-end px-4 pb-12 sm:px-6 lg:px-8">
              <div className="mx-auto max-w-4xl w-full">
                {post.tags && post.tags.length > 0 && (
                  <div className="flex items-center gap-2 mb-4">
                    {post.tags.map((tag) => (
                      <span key={tag} className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-terracotta text-white">
                        <Tag className="w-3 h-3" />{tag}
                      </span>
                    ))}
                  </div>
                )}
                <h1 className="text-3xl font-bold text-[#FAF7F2] sm:text-4xl lg:text-5xl leading-tight" style={{ fontFamily: "var(--font-playfair)" }}>
                  {post.title}
                </h1>
                <div className="mt-4 flex flex-wrap items-center gap-4 text-sm text-[#FAF7F2]/70">
                  <span className="flex items-center gap-1.5"><Calendar className="h-4 w-4" />{formattedDate}</span>
                  <span className="flex items-center gap-1.5"><Clock className="h-4 w-4" />{readTime}</span>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="bg-secondary border-b border-border py-16 px-4 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-4xl">
              {post.tags && post.tags.length > 0 && (
                <div className="flex items-center gap-2 mb-4">
                  {post.tags.map((tag) => (
                    <span key={tag} className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-terracotta/10 text-terracotta">
                      <Tag className="w-3 h-3" />{tag}
                    </span>
                  ))}
                </div>
              )}
              <h1 className="text-3xl font-bold text-foreground sm:text-4xl lg:text-5xl leading-tight" style={{ fontFamily: "var(--font-playfair)" }}>
                {post.title}
              </h1>
              <div className="mt-4 flex flex-wrap items-center gap-4 text-sm text-muted">
                <span className="flex items-center gap-1.5"><Calendar className="h-4 w-4" />{formattedDate}</span>
                <span className="flex items-center gap-1.5"><Clock className="h-4 w-4" />{readTime}</span>
              </div>
            </div>
          </div>
        )}
      </section>

      {/* Content */}
      <section className="flex-1 py-12 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-4xl">
          <div className="flex items-center justify-between mb-8">
            <Link href="/blog" className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-terracotta transition-colors">
              <ArrowLeft className="h-4 w-4" />
              Back to Blog
            </Link>
            <button
              onClick={handleDelete}
              disabled={deleting}
              className="inline-flex items-center gap-1.5 text-sm text-red hover:text-red/80 transition-colors disabled:opacity-40"
            >
              {deleting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
              Delete Post
            </button>
          </div>

          <article className="prose-ghost text-foreground/90 leading-relaxed">
            <BlogContent content={post.content} />
          </article>
        </div>
      </section>

      {/* Related Posts */}
      {related.length > 0 && (
        <section className="py-12 px-4 sm:px-6 lg:px-8 bg-secondary/50">
          <div className="mx-auto max-w-7xl">
            <h2 className="text-2xl font-bold text-foreground text-center mb-8" style={{ fontFamily: "var(--font-playfair)" }}>
              More Posts
            </h2>
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {related.map((p) => (
                <BlogCard key={p.slug} post={p} />
              ))}
            </div>
          </div>
        </section>
      )}

      <footer className="border-t border-border px-6 py-4 bg-foreground text-background">
        <div className="max-w-7xl mx-auto flex items-center justify-between text-xs text-background/60">
          <span>GhostPen - AI writes, you own it</span>
          <span>Powered by GPT-OSS 120B</span>
        </div>
      </footer>
    </div>
  );
}
