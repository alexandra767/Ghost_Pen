"use client";

import { useState } from "react";
import { BlogCard } from "./BlogCard";
import type { BlogPostAPI } from "@/lib/api";

interface BlogListProps {
  posts: BlogPostAPI[];
  onPostDeleted?: () => void;
}

export function BlogList({ posts, onPostDeleted }: BlogListProps) {
  const [activeTag, setActiveTag] = useState("All");

  const allTags = Array.from(new Set(posts.flatMap((p) => p.tags || []))).sort();
  const filterTags = ["All", ...allTags];

  const filtered =
    activeTag === "All"
      ? posts
      : posts.filter((post) => post.tags?.includes(activeTag));

  return (
    <>
      {/* Tag Filter - Bougie Coffee style pills */}
      {allTags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-8">
          {filterTags.map((tag) => (
            <button
              key={tag}
              onClick={() => setActiveTag(tag)}
              className={`px-4 py-2 rounded-full text-sm transition-all ${
                activeTag === tag
                  ? "bg-foreground text-background"
                  : "bg-secondary text-foreground/70 hover:bg-surface-hover"
              }`}
            >
              {tag}
            </button>
          ))}
        </div>
      )}

      {/* Post Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {filtered.map((post) => (
          <BlogCard key={post.slug} post={post} onDeleted={onPostDeleted} />
        ))}
      </div>

      {filtered.length === 0 && (
        <p className="text-center text-muted py-12">
          {posts.length === 0
            ? "No blog posts yet. Generate some content from the dashboard!"
            : "No posts match this tag. Try a different one."}
        </p>
      )}
    </>
  );
}
