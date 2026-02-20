#!/usr/bin/env python3
"""
Alexandra Social Content Engine - FastAPI Server

Provides a REST API for generating and posting content.
Runs on port 8001 (model server uses 8000).

Start: python server.py
  or:  uvicorn server:app --host 0.0.0.0 --port 8001

Endpoints:
  POST /generate       - Generate content for a topic
  POST /post/{platform} - Post content to a platform
  GET  /platforms      - List configured platforms
  GET  /health         - Health check
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
from platforms.blog import BlogAdapter
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


@app.on_event("startup")
async def startup():
    """Initialize platform adapters on startup."""
    if SUPABASE_URL and SUPABASE_KEY:
        adapters["blog"] = BlogAdapter(SUPABASE_URL, SUPABASE_KEY)
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
    system = (
        "You are an expert at writing image generation prompts. "
        "Given a piece of written content, create a single descriptive prompt "
        "for generating a matching photograph or illustration. "
        "The prompt should be vivid, specific, and visual. "
        "Focus on mood, lighting, composition, and subject matter. "
        "Output ONLY the image prompt, nothing else. Keep it under 200 words."
    )
    user_msg = f"Create an image generation prompt for this {req.platform} content:\n\n{req.content[:2000]}"

    try:
        async with httpx.AsyncClient(timeout=120) as client:
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


@app.post("/generate-image")
async def generate_image(req: ImageGenerateRequest):
    """Generate an image using Google Gemini API."""
    if not GEMINI_API_KEY:
        raise HTTPException(400, "GEMINI_API_KEY not configured")

    try:
        from google import genai

        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=req.prompt,
        )

        os.makedirs(IMAGES_DIR, exist_ok=True)
        filename = f"ghostpen-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}.png"
        filepath = os.path.join(IMAGES_DIR, filename)

        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    image_bytes = base64.b64decode(part.inline_data.data)
                    with open(filepath, "wb") as f:
                        f.write(image_bytes)
                    return {
                        "image_path": filepath,
                        "image_url": f"/images/{filename}",
                        "filename": filename,
                    }

        raise HTTPException(500, "No image returned from Gemini")
    except ImportError:
        raise HTTPException(500, "google-genai package not installed. Run: pip install google-genai")
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
