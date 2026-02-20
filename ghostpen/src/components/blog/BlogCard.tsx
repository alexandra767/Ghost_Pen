"use client";

import Link from "next/link";
import { Calendar, Clock, Tag, Trash2 } from "lucide-react";
import { getImageUrl, deleteBlogPost, type BlogPostAPI } from "@/lib/api";

interface BlogCardProps {
  post: BlogPostAPI;
  onDeleted?: () => void;
}

export function BlogCard({ post, onDeleted }: BlogCardProps) {
  const formattedDate = new Date(post.published_at || post.created_at).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  const wordCount = post.content.split(/\s+/).length;
  const readTime = `${Math.max(1, Math.ceil(wordCount / 200))} min read`;
  const heroImage = post.image_url ? (post.image_url.startsWith("/images/") ? getImageUrl(post.image_url) : post.image_url) : null;

  const handleDelete = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm("Delete this post?")) return;
    try {
      await deleteBlogPost(post.id);
      onDeleted?.();
    } catch (err) {
      console.error("Delete failed:", err);
    }
  };

  return (
    <Link href={`/blog/${post.slug}`}>
      <article className="group relative bg-surface border-0 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-all duration-300">
        {/* Delete button */}
        {onDeleted && (
          <button
            onClick={handleDelete}
            className="absolute top-3 right-3 z-10 p-1.5 rounded-full bg-white/80 text-red hover:bg-red hover:text-white transition-colors opacity-0 group-hover:opacity-100"
            title="Delete post"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        )}

        {/* Image */}
        {heroImage && (
          <div className="relative h-52 overflow-hidden">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={heroImage}
              alt={post.title}
              className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
            />
            {post.tags && post.tags.length > 0 && (
              <div className="absolute top-3 left-3">
                <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-terracotta/90 text-white">
                  <Tag className="w-3 h-3" />
                  {post.tags[0]}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Content */}
        <div className="p-5">
          {!heroImage && post.tags && post.tags.length > 0 && (
            <div className="flex items-center gap-2 mb-3">
              {post.tags.slice(0, 2).map((tag) => (
                <span key={tag} className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-terracotta/10 text-terracotta">
                  <Tag className="w-3 h-3" />{tag}
                </span>
              ))}
            </div>
          )}

          <h3 className="text-lg font-semibold text-foreground group-hover:text-terracotta transition-colors line-clamp-2" style={{ fontFamily: "var(--font-playfair)" }}>
            {post.title}
          </h3>

          <p className="mt-2 text-sm text-muted line-clamp-2 leading-relaxed">
            {post.excerpt}
          </p>

          <div className="mt-4 flex items-center gap-4 text-xs text-muted">
            <span className="flex items-center gap-1"><Calendar className="h-3.5 w-3.5" />{formattedDate}</span>
            <span className="flex items-center gap-1"><Clock className="h-3.5 w-3.5" />{readTime}</span>
          </div>
        </div>
      </article>
    </Link>
  );
}
