import { getBlogPosts } from "@/lib/supabase";
import { BlogList } from "@/components/blog/BlogList";
import { PageHero } from "@/components/shared/PageHero";
import Header from "@/components/layout/Header";
import Link from "next/link";
import { PenLine } from "lucide-react";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Blog - GhostPen",
  description: "AI-generated blog posts written in Alexandra's voice.",
};

export const revalidate = 60;

export default async function BlogPage() {
  const posts = await getBlogPosts();

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <PageHero
        title="Blog"
        subtitle="Thoughts, stories, and ideas — written by AI in my voice."
      />

      <section className="flex-1 py-12 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-6xl">
          {/* Action bar */}
          <div className="flex items-center justify-between mb-8">
            <p className="text-sm text-muted">
              {posts.length} {posts.length === 1 ? "post" : "posts"} published
            </p>
            <Link
              href="/"
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm bg-gold/10 text-gold hover:bg-gold/20 transition-colors"
            >
              <PenLine className="w-4 h-4" />
              Create New Post
            </Link>
          </div>

          <BlogList posts={posts} />
        </div>
      </section>

      <footer className="border-t border-border px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between text-xs text-muted">
          <span>GhostPen - AI writes, you own it</span>
          <span>Powered by GPT-OSS 120B</span>
        </div>
      </footer>
    </div>
  );
}
