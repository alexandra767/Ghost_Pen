"""
Core content generator - calls the fine-tuned GPT-OSS Alexandra model
via OpenAI-compatible API and produces platform-specific content.
"""

import httpx
import re
from typing import Optional, Dict

from config import MODEL_ENDPOINT, MODEL_NAME
from prompts.templates import PLATFORM_PROMPTS, DEFAULTS
from prompts.wanderlink import WANDERLINK_CONTEXT


def strip_emojis(text: str) -> str:
    """Remove emoji characters from text, preserving normal punctuation and dashes."""
    # Only target actual emoji ranges, not general Unicode punctuation
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols extended-A
        "\U0001F004-\U0001F0CF"  # playing cards
        "\U0000FE0F"             # variation selector
        "\U0000200D"             # zero width joiner
        "\U00002B50"             # star
        "\U00002764"             # heart
        "\U00002728"             # sparkles
        "\U00002708"             # airplane
        "\U0000270A-\U0000270D"  # raised fist, hand, pencil
        "\U00002600-\U000026FF"  # misc symbols (sun, cloud, umbrella, etc)
        "\U00002700-\U000027BF"  # dingbats
        "\U0000203C"             # double exclamation
        "\U00002049"             # exclamation question
        "\U00002934-\U00002935"  # arrows
        "\U000025AA-\U000025FE"  # geometric shapes
        "\U00002139"             # info
        "\U00002194-\U000021AA"  # arrows
        "\U00002300-\U000023FF"  # misc technical (hourglass, etc)
        "\U00002460-\U000024FF"  # enclosed alphanumerics
        "\U00002500-\U000025FF"  # box drawing + geometric
        "\U00002660-\U00002668"  # card suits, hot springs
        "\U0000267B"             # recycling
        "\U0000267F"             # wheelchair
        "\U00002692-\U000026A1"  # misc symbols
        "\U00002702-\U000027B0"  # dingbats
        "\U0000FE00-\U0000FE0F"  # variation selectors
        "\U0000200B-\U0000200F"  # zero width chars
        "\U00002066-\U00002069"  # directional chars
        "\U0000E000-\U0000F8FF"  # private use area
        "\U000E0020-\U000E007F"  # tags block
        "]+",
        flags=re.UNICODE,
    )
    # Also strip gender/skin tone modifiers that sneak through
    text = re.sub(r'[\u2640\u2642\u2695\u2696\u2708\u2709\u270A-\u270D\u2744\u2747\u274C\u274E\u2753-\u2755\u2757\u2763\u2795-\u2797\u27A1\u27B0\u27BF]', '', text)
    text = emoji_pattern.sub("", text)
    # Clean up double spaces left behind
    text = re.sub(r"  +", " ", text)
    # Clean up leading/trailing spaces on lines
    text = re.sub(r"^ +", "", text, flags=re.MULTILINE)
    return text.strip()


class ContentGenerator:
    """Generate social media content using fine-tuned GPT-OSS Alexandra model."""

    def __init__(self, endpoint: str = None, model_name: str = None):
        self.endpoint = (endpoint or MODEL_ENDPOINT).rstrip("/")
        self.model_name = model_name or MODEL_NAME
        self.api_url = f"{self.endpoint}/v1/chat/completions"

    async def _web_search(self, topic: str) -> str:
        """Search the web for current info on a topic to enrich content."""
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                # Use DuckDuckGo HTML search (no API key needed)
                resp = await client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": topic},
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                if resp.status_code != 200:
                    return ""

                # Extract text snippets from results
                import re as _re
                snippets = _re.findall(
                    r'<a class="result__snippet"[^>]*>(.*?)</a>',
                    resp.text,
                    _re.DOTALL,
                )
                if not snippets:
                    # Try alternate pattern
                    snippets = _re.findall(
                        r'class="result__snippet">(.*?)</(?:a|span)>',
                        resp.text,
                        _re.DOTALL,
                    )

                # Clean HTML tags from snippets
                clean = []
                for s in snippets[:5]:
                    s = _re.sub(r"<[^>]+>", "", s).strip()
                    if s:
                        clean.append(s)

                if clean:
                    return "CURRENT WEB CONTEXT (use this for up-to-date info):\n" + "\n".join(f"- {s}" for s in clean)
                return ""
        except Exception:
            return ""

    async def generate(
        self,
        topic: str,
        platform: str,
        tone: str = None,
        word_count: int = None,
        image_description: str = None,
        is_wanderlink: bool = False,
    ) -> str:
        """Generate content for a specific platform."""
        if platform not in PLATFORM_PROMPTS:
            raise ValueError(f"Unknown platform: {platform}. "
                           f"Available: {list(PLATFORM_PROMPTS.keys())}")

        prompt_config = PLATFORM_PROMPTS[platform]

        # Search the web for current context on the topic
        web_context = await self._web_search(topic)

        # Build template variables with defaults
        template_vars = {
            "topic": topic,
            "tone": tone or DEFAULTS["tone"],
            "word_count": word_count or DEFAULTS["word_count"],
            "image_description": image_description or DEFAULTS["image_description"],
        }

        user_message = prompt_config["template"].format(**template_vars)

        # Inject WanderLink context when topic is about the app
        topic_lower = topic.lower()
        is_wanderlink = is_wanderlink or any(kw in topic_lower for kw in ["wanderlink", "wander link", "wander-link"])

        # Append web context if found (skip for twitter - model returns empty)
        if web_context and platform != "twitter":
            user_message += f"\n\n{web_context}"

        system_prompt = prompt_config["system"]
        if is_wanderlink:
            system_prompt += "\n\n" + WANDERLINK_CONTEXT

            # Force links into the user message per platform
            if platform == "blog":
                user_message += (
                    "\n\nMANDATORY: You MUST include BOTH of these links in the post "
                    "(naturally in the text AND in the conclusion as a call-to-action):\n"
                    "- App Store: https://apps.apple.com/us/app/travel-planner-wanderlink/id6747599042\n"
                    "- Website: https://wander-link.com\n"
                    "Do NOT skip these links. They must appear in the final output."
                )
            elif platform == "instagram":
                user_message += (
                    "\n\nMANDATORY: You MUST include these at the END of the caption "
                    "(BEFORE the hashtags):\n"
                    "Download WanderLink: https://apps.apple.com/us/app/travel-planner-wanderlink/id6747599042\n"
                    "Learn more: https://wander-link.com\n"
                    "Do NOT skip these links. They must appear in the final output."
                )
            elif platform == "twitter":
                user_message += (
                    "\n\nMANDATORY: You MUST include wander-link.com somewhere in the tweet. "
                    "Do NOT skip this link. It must appear in the final output."
                )

        messages = [
            {"role": "developer", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        async with httpx.AsyncClient(timeout=300) as client:
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
            content = result["choices"][0]["message"]["content"]

            # Strip emojis - GPT-OSS ignores prompt instructions about this
            content = strip_emojis(content)

            return content

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
                # Ollama uses / as its health endpoint (returns "Ollama is running")
                resp = await client.get(f"{self.endpoint}/")
                return resp.status_code == 200
        except Exception:
            return False
