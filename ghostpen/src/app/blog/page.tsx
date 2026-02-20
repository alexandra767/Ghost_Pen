"use client";

import { useEffect, useState } from "react";
import { BlogList } from "@/components/blog/BlogList";
import { PageHero } from "@/components/shared/PageHero";
import Header from "@/components/layout/Header";
import Link from "next/link";
import { PenLine, Loader2 } from "lucide-react";
import { getBlogPostsAPI, type BlogPostAPI } from "@/lib/api";

export default function BlogPage() {
  const [posts, setPosts] = useState<BlogPostAPI[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchPosts = async () => {
    try {
      const data = await getBlogPostsAPI();
      setPosts(data);
    } catch (err) {
      console.error("Failed to fetch posts:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPosts();
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header />
      <PageHero
        title="Blog"
        subtitle="Thoughts, stories, and ideas — written by AI in my voice."
      />

      <section className="flex-1 py-12 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          {/* Action bar */}
          <div className="flex items-center justify-between mb-8">
            <p className="text-sm text-muted">
              {loading ? "Loading..." : `${posts.length} ${posts.length === 1 ? "post" : "posts"} published`}
            </p>
            <Link
              href="/"
              className="flex items-center gap-2 px-4 py-2 rounded-full text-sm bg-terracotta text-white hover:bg-terracotta-dark transition-colors"
            >
              <PenLine className="w-4 h-4" />
              Create New Post
            </Link>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-6 h-6 animate-spin text-terracotta" />
            </div>
          ) : (
            <BlogList posts={posts} onPostDeleted={fetchPosts} />
          )}
        </div>
      </section>

      <footer className="border-t border-border px-6 py-4 bg-foreground text-background">
        <div className="max-w-7xl mx-auto flex items-center justify-between text-xs text-background/60">
          <span>GhostPen - AI writes, you own it</span>
          <span>Powered by GPT-OSS 120B</span>
        </div>
      </footer>
    </div>
  );
}
