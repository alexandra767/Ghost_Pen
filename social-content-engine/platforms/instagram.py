"""
Instagram platform adapter using Instagrapi (private API).

Requirements:
  pip install instagrapi

Setup:
  Set environment variables: INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD

Notes:
  - Instagram requires an image for every post
  - Rate limit yourself to 2-3 posts per day to avoid blocks
  - Session is persisted to avoid repeated logins
"""

import os
import json
import time
import random
from pathlib import Path

from instagrapi import Client as InstaClient

from .base import PlatformAdapter, PostResult


class InstagramAdapter(PlatformAdapter):
    """Instagram posting via Instagrapi."""

    def __init__(
        self,
        username: str,
        password: str,
        session_file: str = None,
    ):
        self.client = InstaClient()
        self.username = username
        self.password = password
        self.session_file = session_file or os.path.expanduser("~/.instagram_session.json")
        self._logged_in = False

    @property
    def platform_name(self) -> str:
        return "instagram"

    @property
    def max_content_length(self) -> int:
        return 2200

    def _login(self):
        """Login with session persistence to avoid repeated auth."""
        if self._logged_in:
            return

        # Try loading existing session
        if os.path.exists(self.session_file):
            try:
                self.client.load_settings(self.session_file)
                self.client.login(self.username, self.password)
                self._logged_in = True
                return
            except Exception:
                # Session expired, do fresh login
                pass

        # Fresh login
        self.client.login(self.username, self.password)
        self.client.dump_settings(self.session_file)
        self._logged_in = True

    async def post(
        self,
        content: str,
        image_path: str = None,
        **kwargs,
    ) -> PostResult:
        """Post a photo with caption to Instagram."""
        if not image_path:
            return PostResult(
                success=False,
                platform="instagram",
                error="Instagram requires an image. Provide --image path.",
            )

        if not os.path.exists(image_path):
            return PostResult(
                success=False,
                platform="instagram",
                error=f"Image not found: {image_path}",
            )

        self._login()

        # Truncate caption if needed
        caption = content[:2200]

        # Small random delay to be more human-like
        time.sleep(random.uniform(1, 3))

        try:
            media = self.client.photo_upload(
                path=Path(image_path),
                caption=caption,
            )
            return PostResult(
                success=True,
                platform="instagram",
                post_id=str(media.pk),
                url=f"https://www.instagram.com/p/{media.code}/",
            )
        except Exception as e:
            return PostResult(success=False, platform="instagram", error=str(e))

    async def validate_credentials(self) -> bool:
        """Check Instagram login."""
        try:
            self._login()
            return True
        except Exception:
            return False
