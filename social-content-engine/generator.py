"""
Core content generator - calls the fine-tuned GPT-OSS Alexandra model
via OpenAI-compatible API and produces platform-specific content.
"""

import httpx
from typing import Optional, Dict

from config import MODEL_ENDPOINT, MODEL_NAME
from prompts.templates import PLATFORM_PROMPTS, DEFAULTS


class ContentGenerator:
    """Generate social media content using fine-tuned GPT-OSS Alexandra model."""

    def __init__(self, endpoint: str = None, model_name: str = None):
        self.endpoint = (endpoint or MODEL_ENDPOINT).rstrip("/")
        self.model_name = model_name or MODEL_NAME
        self.api_url = f"{self.endpoint}/v1/chat/completions"

    async def generate(
        self,
        topic: str,
        platform: str,
        tone: str = None,
        word_count: int = None,
        image_description: str = None,
    ) -> str:
        """Generate content for a specific platform."""
        if platform not in PLATFORM_PROMPTS:
            raise ValueError(f"Unknown platform: {platform}. "
                           f"Available: {list(PLATFORM_PROMPTS.keys())}")

        prompt_config = PLATFORM_PROMPTS[platform]

        # Build template variables with defaults
        template_vars = {
            "topic": topic,
            "tone": tone or DEFAULTS["tone"],
            "word_count": word_count or DEFAULTS["word_count"],
            "image_description": image_description or DEFAULTS["image_description"],
        }

        user_message = prompt_config["template"].format(**template_vars)

        messages = [
            {"role": "developer", "content": prompt_config["system"]},
            {"role": "user", "content": user_message},
        ]

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                self.api_url,
                json={
                    "model": self.model_name,
                    "messages": messages,
                    "max_tokens": prompt_config["max_tokens"],
                    "temperature": prompt_config["temperature"],
                    "top_p": 0.95,
                },
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]

    async def generate_all(
        self,
        topic: str,
        tone: str = None,
        word_count: int = None,
        image_description: str = None,
    ) -> Dict[str, str]:
        """Generate content for all platforms from one topic."""
        results = {}
        for platform in PLATFORM_PROMPTS:
            results[platform] = await self.generate(
                topic=topic,
                platform=platform,
                tone=tone,
                word_count=word_count,
                image_description=image_description,
            )
        return results

    async def health_check(self) -> bool:
        """Check if the model server is reachable."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.endpoint}/health")
                return resp.status_code == 200
        except Exception:
            return False
