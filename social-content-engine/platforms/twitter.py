"""
Twitter/X platform adapter using Tweepy v2 API.

Requirements:
  pip install tweepy

Setup:
  1. Create a Twitter Developer account at developer.twitter.com
  2. Create a project and app with Read and Write permissions
  3. Generate consumer keys and access tokens
  4. Set environment variables:
     TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET,
     TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET
"""

import tweepy

from .base import PlatformAdapter, PostResult


class TwitterAdapter(PlatformAdapter):
    """Twitter/X posting via Tweepy v2 API."""

    def __init__(
        self,
        consumer_key: str,
        consumer_secret: str,
        access_token: str,
        access_token_secret: str,
    ):
        self.client = tweepy.Client(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
        )

    @property
    def platform_name(self) -> str:
        return "twitter"

    @property
    def max_content_length(self) -> int:
        return 280

    async def post(self, content: str, **kwargs) -> PostResult:
        """Post a tweet."""
        # Truncate if over limit
        if len(content) > 280:
            content = content[:277] + "..."

        try:
            response = self.client.create_tweet(text=content)
            tweet_id = response.data["id"]
            return PostResult(
                success=True,
                platform="twitter",
                post_id=str(tweet_id),
                url=f"https://x.com/i/status/{tweet_id}",
            )
        except Exception as e:
            return PostResult(success=False, platform="twitter", error=str(e))

    async def validate_credentials(self) -> bool:
        """Verify Twitter API credentials."""
        try:
            self.client.get_me()
            return True
        except Exception:
            return False
