"use client";

import Link from "next/link";
import Image from "next/image";
import { Calendar, Clock, Tag } from "lucide-react";
import type { BlogPost } from "@/lib/supabase";

interface BlogCardProps {
  post: BlogPost;
}

export function BlogCard({ post }: BlogCardProps) {
  const formattedDate = new Date(post.publishedAt).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  return (
    <Link href={`/blog/${post.slug}`}>
      <article className="group bg-surface border border-border rounded-xl overflow-hidden hover:border-gold/30 transition-all duration-300">
        {/* Image */}
        {post.imageUrl && (
          <div className="relative h-48 overflow-hidden">
            <Image
              src={post.imageUrl}
              alt={post.title}
              fill
              className="object-cover transition-transform duration-500 group-hover:scale-105"
            />
          </div>
        )}

        {/* Content */}
        <div className="p-5">
          {/* Tags */}
          {post.tags.length > 0 && (
            <div className="flex items-center gap-2 mb-3">
              {post.tags.slice(0, 2).map((tag) => (
                <span
                  key={tag}
                  className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-gold/10 text-gold"
                >
                  <Tag className="w-3 h-3" />
                  {tag}
                </span>
              ))}
            </div>
          )}

          {/* Title */}
          <h3
            className="text-lg font-semibold text-foreground group-hover:text-gold transition-colors line-clamp-2"
            style={{ fontFamily: "var(--font-space)" }}
          >
            {post.title}
          </h3>

          {/* Excerpt */}
          <p className="mt-2 text-sm text-muted line-clamp-3 leading-relaxed">
            {post.excerpt}
          </p>

          {/* Meta */}
          <div className="mt-4 flex items-center gap-4 text-xs text-muted">
            <span className="flex items-center gap-1">
              <Calendar className="h-3.5 w-3.5" />
              {formattedDate}
            </span>
            <span className="flex items-center gap-1">
              <Clock className="h-3.5 w-3.5" />
              {post.readTime}
            </span>
          </div>
        </div>
      </article>
    </Link>
  );
}
