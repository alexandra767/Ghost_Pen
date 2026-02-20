"use client";

import { useState } from "react";
import { BlogCard } from "./BlogCard";
import type { BlogPost } from "@/lib/supabase";

interface BlogListProps {
  posts: BlogPost[];
}

export function BlogList({ posts }: BlogListProps) {
  const [activeTag, setActiveTag] = useState("All");

  // Collect all unique tags
  const allTags = Array.from(new Set(posts.flatMap((p) => p.tags))).sort();
  const filterTags = ["All", ...allTags];

  const filtered =
    activeTag === "All"
      ? posts
      : posts.filter((post) => post.tags.includes(activeTag));

  return (
    <>
      {/* Tag Filter */}
      {allTags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-8">
          {filterTags.map((tag) => (
            <button
              key={tag}
              onClick={() => setActiveTag(tag)}
              className={`px-3 py-1.5 rounded-lg text-sm transition-all ${
                activeTag === tag
                  ? "bg-gold/10 border border-gold/30 text-gold"
                  : "bg-surface border border-border text-muted hover:text-foreground hover:bg-surface-hover"
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
          <BlogCard key={post.slug} post={post} />
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
