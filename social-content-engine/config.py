"""
Configuration for the Social Content Engine.
All sensitive values are loaded from environment variables.
"""

import os

# Model endpoint - defaults to Ollama's OpenAI-compatible API
MODEL_ENDPOINT = os.getenv("MODEL_ENDPOINT", "http://localhost:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-oss:120b")

# Supabase (blog)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Twitter/X (Tweepy v2)
TWITTER_CONSUMER_KEY = os.getenv("TWITTER_CONSUMER_KEY", "")
TWITTER_CONSUMER_SECRET = os.getenv("TWITTER_CONSUMER_SECRET", "")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")

# Instagram (Instagrapi)
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME", "")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD", "")
INSTAGRAM_SESSION_FILE = os.path.expanduser("~/.instagram_session.json")

# Gemini API (for image generation)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Generated images directory
IMAGES_DIR = os.path.expanduser("~/generated_imgs")

# Content engine API port
ENGINE_PORT = int(os.getenv("ENGINE_PORT", "8001"))
