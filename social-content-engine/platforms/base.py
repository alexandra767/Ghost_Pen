"""
Abstract base class for platform adapters.
Implement this to add a new social media platform.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class PostResult:
    """Result from posting content to a platform."""
    success: bool
    platform: str = ""
    post_id: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None


class PlatformAdapter(ABC):
    """Base class for all platform integrations.

    To add a new platform:
      1. Create a new file in platforms/ (e.g., linkedin.py)
      2. Subclass PlatformAdapter
      3. Implement post(), validate_credentials(), platform_name, max_content_length
      4. Register it in cli.py and server.py
    """

    @abstractmethod
    async def post(self, content: str, **kwargs) -> PostResult:
        """Post content to the platform."""
        pass

    @abstractmethod
    async def validate_credentials(self) -> bool:
        """Check if API credentials are valid and working."""
        pass

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Short name for this platform (e.g., 'twitter', 'blog')."""
        pass

    @property
    @abstractmethod
    def max_content_length(self) -> int:
        """Maximum content length in characters."""
        pass
