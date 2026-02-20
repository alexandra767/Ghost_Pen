"""
Supabase blog platform adapter.
Stores blog posts in a Supabase PostgreSQL database.

Required Supabase table (run this SQL in Supabase SQL Editor):

    CREATE TABLE blog_posts (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        title TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        content TEXT NOT NULL,
        excerpt TEXT,
        tags TEXT[] DEFAULT '{}',
        status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),
        published_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );

    ALTER TABLE blog_posts ENABLE ROW LEVEL SECURITY;

    CREATE POLICY "Public can read published posts"
    ON blog_posts FOR SELECT USING (status = 'published');

    CREATE POLICY "Service role can manage posts"
    ON blog_posts FOR ALL USING (true);
"""

import re
from datetime import datetime, timezone
from typing import Optional, List

from supabase import create_client

from .base import PlatformAdapter, PostResult


class BlogAdapter(PlatformAdapter):
    """Supabase-backed blog platform."""

    def __init__(self, supabase_url: str, supabase_key: str):
        self.client = create_client(supabase_url, supabase_key)

    @property
    def platform_name(self) -> str:
        return "blog"

    @property
    def max_content_length(self) -> int:
        return 50000

    def _slugify(self, title: str) -> str:
        slug = title.lower().strip()
        slug = re.sub(r"[^a-z0-9\s-]", "", slug)
        slug = re.sub(r"[\s-]+", "-", slug).strip("-")
        return slug

    def _extract_title(self, content: str) -> str:
        """Extract title from markdown content (first # heading)."""
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("#"):
                return line.lstrip("#").strip()
        return "Untitled Post"

    def _make_excerpt(self, content: str, max_len: int = 200) -> str:
        """Create excerpt from content, stripping markdown."""
        # Skip title line
        lines = content.split("\n")
        text_lines = [
            l for l in lines
            if l.strip() and not l.strip().startswith("#")
        ]
        text = " ".join(text_lines)
        # Strip markdown formatting
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"\*(.+?)\*", r"\1", text)
        text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)
        if len(text) > max_len:
            text = text[:max_len].rsplit(" ", 1)[0] + "..."
        return text

    async def post(
        self,
        content: str,
        title: str = "",
        tags: List[str] = None,
        publish: bool = False,
        **kwargs,
    ) -> PostResult:
        """Create a blog post in Supabase."""
        if not title:
            title = self._extract_title(content)

        slug = self._slugify(title)
        excerpt = self._make_excerpt(content)

        data = {
            "title": title,
            "slug": slug,
            "content": content,
            "excerpt": excerpt,
            "tags": tags or [],
            "status": "published" if publish else "draft",
        }

        if publish:
            data["published_at"] = datetime.now(timezone.utc).isoformat()

        try:
            result = self.client.table("blog_posts").insert(data).execute()
            if result.data:
                post = result.data[0]
                return PostResult(
                    success=True,
                    platform="blog",
                    post_id=post["id"],
                    url=f"/blog/{post['slug']}",
                )
            return PostResult(success=False, platform="blog", error="Insert returned no data")
        except Exception as e:
            return PostResult(success=False, platform="blog", error=str(e))

    async def validate_credentials(self) -> bool:
        """Check Supabase connection by querying the table."""
        try:
            self.client.table("blog_posts").select("id").limit(1).execute()
            return True
        except Exception:
            return False
