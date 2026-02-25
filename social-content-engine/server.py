#!/usr/bin/env python3
"""
Alexandra Social Content Engine - FastAPI Server

Provides a REST API for generating and posting content.
Runs on port 8001 (model server uses 8000).

Start: python server.py
  or:  uvicorn server:app --host 0.0.0.0 --port 8001
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import uvicorn
import httpx
import os
import base64
import uuid
from datetime import datetime

from config import (
    SUPABASE_URL, SUPABASE_KEY,
    TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET,
    TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET,
    INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD,
    GEMINI_API_KEY, IMAGES_DIR,
    ENGINE_PORT,
)
from generator import ContentGenerator
from platforms.blog import BlogAdapter, LocalBlogStore
from platforms.twitter import TwitterAdapter
from platforms.instagram import InstagramAdapter
from platforms.base import PlatformAdapter

app = FastAPI(title="Alexandra Content Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize
generator = ContentGenerator()
adapters: Dict[str, PlatformAdapter] = {}
blog_store = None  # Will be BlogAdapter or LocalBlogStore


@app.on_event("startup")
async def startup():
    global blog_store
    """Initialize platform adapters on startup."""
    if SUPABASE_URL and SUPABASE_KEY:
        blog_adapter = BlogAdapter(SUPABASE_URL, SUPABASE_KEY)
        adapters["blog"] = blog_adapter
        blog_store = blog_adapter
        print("Blog: Using Supabase")
    else:
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        local_store = LocalBlogStore(data_dir)
        adapters["blog"] = local_store
        blog_store = local_store
        print("Blog: Using local JSON storage (Supabase not configured)")

    if TWITTER_CONSUMER_KEY and TWITTER_ACCESS_TOKEN:
        adapters["twitter"] = TwitterAdapter(
            TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET,
            TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET,
        )
    if INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD:
        adapters["instagram"] = InstagramAdapter(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)

    print(f"Configured platforms: {list(adapters.keys()) or 'none'}")


# === Request/Response Models ===

class GenerateRequest(BaseModel):
    topic: str
    platform: str = "all"  # blog, twitter, instagram, all
    tone: str = "casual"
    word_count: int = 500
    image_description: Optional[str] = None
    auto_post: bool = False
    image_path: Optional[str] = None  # For Instagram posting
    is_wanderlink: bool = False  # Force WanderLink context injection

class GenerateResponse(BaseModel):
    content: Dict[str, str] = {}
    posted: Dict[str, dict] = {}

class PostRequest(BaseModel):
    content: str
    title: Optional[str] = None
    image_path: Optional[str] = None
    image_url: Optional[str] = None
    tags: Optional[List[str]] = None


# === Endpoints ===

@app.post("/generate", response_model=GenerateResponse)
async def generate_content(req: GenerateRequest):
    """Generate content for one or all platforms."""
    platforms = (
        ["blog", "twitter", "instagram"] if req.platform == "all"
        else [req.platform]
    )

    content = {}
    for platform in platforms:
        try:
            content[platform] = await generator.generate(
                topic=req.topic,
                platform=platform,
                tone=req.tone,
                word_count=req.word_count,
                image_description=req.image_description,
                is_wanderlink=req.is_wanderlink,
            )
        except Exception as e:
            content[platform] = f"[ERROR: {e}]"

    posted = {}
    if req.auto_post:
        for platform, text in content.items():
            if platform not in adapters:
                posted[platform] = {"success": False, "error": "not configured"}
                continue

            kwargs = {}
            if platform == "instagram":
                if not req.image_path:
                    posted[platform] = {"success": False, "error": "no image provided"}
                    continue
                kwargs["image_path"] = req.image_path
            if platform == "blog":
                kwargs["publish"] = True

            result = await adapters[platform].post(text, **kwargs)
            posted[platform] = {
                "success": result.success,
                "post_id": result.post_id,
                "url": result.url,
                "error": result.error,
            }

    return GenerateResponse(content=content, posted=posted)


@app.post("/post/{platform}")
async def post_content(platform: str, req: PostRequest):
    """Post pre-written content to a specific platform."""
    if platform not in adapters:
        raise HTTPException(404, f"Platform '{platform}' not configured")

    kwargs = {}
    if platform == "instagram":
        if not req.image_path:
            raise HTTPException(400, "Instagram requires image_path")
        kwargs["image_path"] = req.image_path
    if platform == "blog":
        kwargs["title"] = req.title or ""
        kwargs["tags"] = req.tags or []
        kwargs["publish"] = True
        if req.image_url:
            kwargs["image_url"] = req.image_url

    result = await adapters[platform].post(req.content, **kwargs)
    return {
        "success": result.success,
        "platform": platform,
        "post_id": result.post_id,
        "url": result.url,
        "error": result.error,
    }


# === Blog Read/Delete Endpoints ===

@app.get("/api/blog/posts")
async def get_blog_posts():
    """Get all published blog posts."""
    if not blog_store:
        return []
    posts = await blog_store.get_posts()
    return posts


@app.get("/api/blog/posts/{slug}")
async def get_blog_post(slug: str):
    """Get a single blog post by slug."""
    if not blog_store:
        raise HTTPException(404, "Blog not configured")
    post = await blog_store.get_post_by_slug(slug)
    if not post:
        raise HTTPException(404, "Post not found")
    return post


@app.delete("/api/blog/posts/{post_id}")
async def delete_blog_post(post_id: str):
    """Delete a blog post by ID."""
    if not blog_store:
        raise HTTPException(404, "Blog not configured")
    success = await blog_store.delete_post(post_id)
    if not success:
        raise HTTPException(404, "Post not found")
    return {"success": True, "deleted": post_id}


@app.get("/platforms")
async def list_platforms():
    """List configured platforms and their status."""
    status = {}
    for name, adapter in adapters.items():
        try:
            ok = await adapter.validate_credentials()
            status[name] = {"configured": True, "valid": ok}
        except Exception as e:
            status[name] = {"configured": True, "valid": False, "error": str(e)}

    for name in ["blog", "twitter", "instagram"]:
        if name not in status:
            status[name] = {"configured": False, "valid": False}

    return status


@app.get("/topics/wanderlink")
async def wanderlink_topics():
    """Get suggested WanderLink content topics."""
    from prompts.wanderlink import WANDERLINK_TOPICS
    return {"topics": WANDERLINK_TOPICS}


@app.get("/health")
async def health():
    model_ok = await generator.health_check()
    return {
        "status": "ok",
        "model_server": "ok" if model_ok else "unreachable",
        "platforms": list(adapters.keys()),
        "image_generation": bool(GEMINI_API_KEY),
    }


# === Image Generation Endpoints ===

class ImagePromptRequest(BaseModel):
    content: str
    platform: str = "blog"

class ImageGenerateRequest(BaseModel):
    prompt: str


@app.post("/generate-image-prompt")
async def generate_image_prompt(req: ImagePromptRequest):
    """Use GPT-OSS to create an image generation prompt from content."""
    # Detect if content is about WanderLink
    content_lower = req.content.lower()
    is_wanderlink = any(kw in content_lower for kw in ["wanderlink", "wander link", "wander-link"])

    system = (
        "You are an expert at writing image generation prompts. "
        "Given a piece of written content, create a single descriptive prompt "
        "for generating a matching photograph or illustration. "
        "The prompt should be vivid, specific, and visual. "
        "Focus on mood, lighting, composition, and subject matter. "
        "Output ONLY the image prompt, nothing else. Keep it under 200 words."
    )

    if is_wanderlink:
        system += (
            "\n\nIMPORTANT: This content is about WanderLink, a travel planning app. "
            "The image should be TRAVEL-FOCUSED and relevant to the specific topic. "
            "Think: stunning travel destinations, a traveler exploring a beautiful city, "
            "a person discovering a hidden gem cafe or scenic overlook, someone planning "
            "a trip with a phone showing a map, a solo traveler at an amazing viewpoint, "
            "golden hour at a famous landmark, cozy street scenes in a foreign city, "
            "or an adventurer with a backpack overlooking a breathtaking landscape. "
            "Match the image to the SPECIFIC feature or travel scenario discussed in the content. "
            "For example: if the content is about hidden gems, show an off-the-beaten-path discovery; "
            "if about safety features, show a confident solo traveler; "
            "if about AI trip planning, show a traveler with an itinerary at a destination. "
            "Style: high-quality travel photography, warm natural lighting, aspirational but authentic. "
            "Do NOT generate screenshots, app mockups, or UI elements — generate beautiful travel scenes."
        )

    user_msg = f"Create an image generation prompt for this {req.platform} content:\n\n{req.content[:2000]}"

    try:
        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(
                generator.api_url,
                json={
                    "model": generator.model_name,
                    "messages": [
                        {"role": "developer", "content": system},
                        {"role": "user", "content": user_msg},
                    ],
                    "max_tokens": 300,
                    "temperature": 0.7,
                },
            )
            response.raise_for_status()
            result = response.json()
            image_prompt = result["choices"][0]["message"]["content"].strip()
            return {"image_prompt": image_prompt}
    except Exception as e:
        raise HTTPException(500, f"Failed to generate image prompt: {e}")


def _clean_image_prompt(prompt: str) -> str:
    """Clean up GPT-OSS image prompts - strip markdown, keep it simple for Gemini."""
    import re as _re
    prompt = _re.sub(r'\*\*([^*]+)\*\*', r'\1', prompt)
    prompt = _re.sub(r'\*([^*]+)\*', r'\1', prompt)
    prompt = _re.sub(r'```[^`]*```', '', prompt, flags=_re.DOTALL)
    prompt = _re.sub(r'`([^`]+)`', r'\1', prompt)
    prompt = _re.sub(r'^#+\s+', '', prompt, flags=_re.MULTILINE)
    prompt = _re.sub(r'^[-*]\s+', '', prompt, flags=_re.MULTILINE)
    prompt = _re.sub(r'\n{2,}', ' ', prompt)
    prompt = prompt.strip()
    if len(prompt) > 300:
        prompt = prompt[:300]
    return prompt


@app.post("/generate-image")
async def generate_image(req: ImageGenerateRequest):
    """Generate an image using Google Gemini REST API."""
    if not GEMINI_API_KEY:
        raise HTTPException(400, "GEMINI_API_KEY not configured")

    clean_prompt = _clean_image_prompt(req.prompt)

    try:
        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key={GEMINI_API_KEY}",
                json={
                    "contents": [{"parts": [{"text": f"Generate an image: {clean_prompt}"}]}],
                    "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
                },
            )
            resp.raise_for_status()
            data = resp.json()

        os.makedirs(IMAGES_DIR, exist_ok=True)
        filename = f"ghostpen-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}.png"
        filepath = os.path.join(IMAGES_DIR, filename)

        if "candidates" in data and data["candidates"]:
            for part in data["candidates"][0]["content"]["parts"]:
                if "inlineData" in part and part["inlineData"]["mimeType"].startswith("image/"):
                    img_data = base64.b64decode(part["inlineData"]["data"])
                    with open(filepath, "wb") as f:
                        f.write(img_data)
                    return {
                        "image_path": filepath,
                        "image_url": f"/images/{filename}",
                        "filename": filename,
                    }

        raise HTTPException(500, "No image returned from Gemini")
    except httpx.TimeoutException:
        raise HTTPException(504, "Image generation timed out. Try a simpler topic.")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(500, f"Image generation failed: {e}")


@app.get("/images/{filename}")
async def serve_image(filename: str):
    """Serve generated images."""
    filepath = os.path.join(IMAGES_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(404, "Image not found")
    return FileResponse(filepath, media_type="image/png")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=ENGINE_PORT)
