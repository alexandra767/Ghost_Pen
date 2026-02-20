"""
Blog platform adapter with Supabase + local JSON fallback.

When Supabase is configured, uses it as the primary store.
When not configured, falls back to a local JSON file so the
blog works out-of-the-box without any external services.
"""

import json
import re
import os
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from .base import PlatformAdapter, PostResult


class BlogAdapter(PlatformAdapter):
    """Supabase-backed blog platform."""

    def __init__(self, supabase_url: str, supabase_key: str):
        from supabase import create_client
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
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("#"):
                return line.lstrip("#").strip()
        return "Untitled Post"

    def _make_excerpt(self, content: str, max_len: int = 200) -> str:
        lines = content.split("\n")
        text_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]
        text = " ".join(text_lines)
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"\*(.+?)\*", r"\1", text)
        text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)
        if len(text) > max_len:
            text = text[:max_len].rsplit(" ", 1)[0] + "..."
        return text

    async def post(self, content: str, title: str = "", tags: List[str] = None,
                   publish: bool = False, image_url: str = "", **kwargs) -> PostResult:
        if not title:
            title = self._extract_title(content)
        slug = self._slugify(title)
        excerpt = self._make_excerpt(content)
        data = {
            "title": title, "slug": slug, "content": content, "excerpt": excerpt,
            "tags": tags or [], "status": "published" if publish else "draft",
        }
        if image_url:
            data["image_url"] = image_url
        if publish:
            data["published_at"] = datetime.now(timezone.utc).isoformat()
        try:
            result = self.client.table("blog_posts").insert(data).execute()
            if result.data:
                post = result.data[0]
                return PostResult(success=True, platform="blog", post_id=post["id"], url=f"/blog/{post['slug']}")
            return PostResult(success=False, platform="blog", error="Insert returned no data")
        except Exception as e:
            return PostResult(success=False, platform="blog", error=str(e))

    async def get_posts(self) -> list:
        try:
            result = self.client.table("blog_posts").select("*").eq("status", "published").order("published_at", desc=True).execute()
            return result.data or []
        except Exception:
            return []

    async def get_post_by_slug(self, slug: str) -> Optional[dict]:
        try:
            result = self.client.table("blog_posts").select("*").eq("slug", slug).eq("status", "published").single().execute()
            return result.data
        except Exception:
            return None

    async def delete_post(self, post_id: str) -> bool:
        try:
            self.client.table("blog_posts").delete().eq("id", post_id).execute()
            return True
        except Exception:
            return False

    async def validate_credentials(self) -> bool:
        try:
            self.client.table("blog_posts").select("id").limit(1).execute()
            return True
        except Exception:
            return False


class LocalBlogStore(PlatformAdapter):
    """Local JSON file blog store — works without Supabase."""

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.file_path = os.path.join(data_dir, "blog_posts.json")
        os.makedirs(data_dir, exist_ok=True)
        if not os.path.exists(self.file_path):
            self._save([])

    @property
    def platform_name(self) -> str:
        return "blog"

    @property
    def max_content_length(self) -> int:
        return 50000

    def _load(self) -> list:
        try:
            with open(self.file_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save(self, posts: list):
        with open(self.file_path, "w") as f:
            json.dump(posts, f, indent=2)

    def _slugify(self, title: str) -> str:
        slug = title.lower().strip()
        slug = re.sub(r"[^a-z0-9\s-]", "", slug)
        slug = re.sub(r"[\s-]+", "-", slug).strip("-")
        return slug

    def _extract_title(self, content: str) -> str:
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("#"):
                return line.lstrip("#").strip()
        return "Untitled Post"

    def _make_excerpt(self, content: str, max_len: int = 200) -> str:
        lines = content.split("\n")
        text_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]
        text = " ".join(text_lines)
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"\*(.+?)\*", r"\1", text)
        text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)
        if len(text) > max_len:
            text = text[:max_len].rsplit(" ", 1)[0] + "..."
        return text

    async def post(self, content: str, title: str = "", tags: List[str] = None,
                   publish: bool = False, image_url: str = "", **kwargs) -> PostResult:
        if not title:
            title = self._extract_title(content)
        slug = self._slugify(title)
        # Ensure unique slug
        posts = self._load()
        existing_slugs = {p["slug"] for p in posts}
        base_slug = slug
        counter = 1
        while slug in existing_slugs:
            slug = f"{base_slug}-{counter}"
            counter += 1

        now = datetime.now(timezone.utc).isoformat()
        post = {
            "id": str(uuid.uuid4()),
            "title": title,
            "slug": slug,
            "content": content,
            "excerpt": self._make_excerpt(content),
            "tags": tags or [],
            "image_url": image_url or None,
            "status": "published" if publish else "draft",
            "published_at": now if publish else None,
            "created_at": now,
            "updated_at": now,
        }
        posts.append(post)
        self._save(posts)
        return PostResult(success=True, platform="blog", post_id=post["id"], url=f"/blog/{post['slug']}")

    async def get_posts(self) -> list:
        posts = self._load()
        published = [p for p in posts if p.get("status") == "published"]
        published.sort(key=lambda p: p.get("published_at", ""), reverse=True)
        return published

    async def get_post_by_slug(self, slug: str) -> Optional[dict]:
        posts = self._load()
        for p in posts:
            if p["slug"] == slug and p.get("status") == "published":
                return p
        return None

    async def delete_post(self, post_id: str) -> bool:
        posts = self._load()
        original_len = len(posts)
        posts = [p for p in posts if p["id"] != post_id]
        if len(posts) < original_len:
            self._save(posts)
            return True
        return False

    async def validate_credentials(self) -> bool:
        return True
