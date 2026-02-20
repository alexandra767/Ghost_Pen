#!/usr/bin/env python3
"""
Alexandra Social Content Engine - CLI

Generate and post content to blog, Twitter/X, and Instagram
using a fine-tuned GPT-OSS 120B model.

Usage:
  python cli.py generate "my thoughts on AI" --platform all
  python cli.py generate "fly fishing tips" --platform twitter
  python cli.py generate "camping adventures" --platform blog --tone reflective --post
  python cli.py post twitter --content "Just caught a beautiful trout!"
  python cli.py post instagram --content "Best day ever" --image photo.jpg
  python cli.py status
"""

import argparse
import asyncio
import sys
import json

from config import (
    SUPABASE_URL, SUPABASE_KEY,
    TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET,
    TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET,
    INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD,
)
from generator import ContentGenerator
from platforms.blog import BlogAdapter
from platforms.twitter import TwitterAdapter
from platforms.instagram import InstagramAdapter


def get_platforms():
    """Initialize available platform adapters."""
    adapters = {}

    if SUPABASE_URL and SUPABASE_KEY:
        adapters["blog"] = BlogAdapter(SUPABASE_URL, SUPABASE_KEY)

    if TWITTER_CONSUMER_KEY and TWITTER_ACCESS_TOKEN:
        adapters["twitter"] = TwitterAdapter(
            TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET,
            TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET,
        )

    if INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD:
        adapters["instagram"] = InstagramAdapter(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)

    return adapters


async def cmd_generate(args):
    """Generate content for one or all platforms."""
    gen = ContentGenerator()

    # Check model server
    if not await gen.health_check():
        print("ERROR: Model server not reachable at", gen.endpoint)
        print("Start it with: bash serve_gptoss_alexandra.sh")
        sys.exit(1)

    platforms_to_generate = (
        ["blog", "twitter", "instagram"] if args.platform == "all"
        else [args.platform]
    )

    print(f"Generating content about: {args.topic}")
    print(f"Platforms: {', '.join(platforms_to_generate)}")
    print()

    results = {}
    for platform in platforms_to_generate:
        print(f"--- {platform.upper()} ---")
        content = await gen.generate(
            topic=args.topic,
            platform=platform,
            tone=args.tone,
            word_count=args.word_count,
            image_description=args.image_desc,
        )
        results[platform] = content
        print(content)
        print()

    # Post if requested
    if args.post:
        adapters = get_platforms()
        print("=" * 40)
        print("POSTING...")
        for platform, content in results.items():
            if platform not in adapters:
                print(f"  {platform}: SKIPPED (not configured)")
                continue

            kwargs = {}
            if platform == "instagram" and args.image:
                kwargs["image_path"] = args.image
            elif platform == "instagram":
                print(f"  instagram: SKIPPED (no --image provided)")
                continue
            if platform == "blog":
                kwargs["publish"] = True

            result = await adapters[platform].post(content, **kwargs)
            if result.success:
                print(f"  {platform}: POSTED! {result.url or result.post_id}")
            else:
                print(f"  {platform}: FAILED - {result.error}")

    return results


async def cmd_post(args):
    """Post pre-written content to a platform."""
    adapters = get_platforms()

    if args.platform not in adapters:
        print(f"ERROR: {args.platform} not configured. Set the required env vars.")
        sys.exit(1)

    adapter = adapters[args.platform]

    kwargs = {}
    if args.platform == "instagram":
        if not args.image:
            print("ERROR: Instagram requires --image")
            sys.exit(1)
        kwargs["image_path"] = args.image
    if args.platform == "blog":
        kwargs["title"] = args.title or ""
        kwargs["publish"] = True

    result = await adapter.post(args.content, **kwargs)

    if result.success:
        print(f"Posted to {args.platform}!")
        if result.url:
            print(f"  URL: {result.url}")
        if result.post_id:
            print(f"  ID: {result.post_id}")
    else:
        print(f"Failed: {result.error}")


async def cmd_status(args):
    """Check status of model server and platform connections."""
    gen = ContentGenerator()

    # Model server
    model_ok = await gen.health_check()
    print(f"Model server ({gen.endpoint}): {'OK' if model_ok else 'UNREACHABLE'}")

    # Platforms
    adapters = get_platforms()
    if not adapters:
        print("No platforms configured (set env vars)")
    for name, adapter in adapters.items():
        try:
            ok = await adapter.validate_credentials()
            print(f"{name}: {'OK' if ok else 'INVALID CREDENTIALS'}")
        except Exception as e:
            print(f"{name}: ERROR - {e}")

    unconfigured = {"blog", "twitter", "instagram"} - set(adapters.keys())
    for name in unconfigured:
        print(f"{name}: NOT CONFIGURED")


def main():
    parser = argparse.ArgumentParser(
        description="Alexandra Social Content Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # generate
    gen_p = subparsers.add_parser("generate", help="Generate content from a topic")
    gen_p.add_argument("topic", help="What to write about")
    gen_p.add_argument("-p", "--platform", default="all",
                       choices=["blog", "twitter", "instagram", "all"])
    gen_p.add_argument("--tone", default="casual",
                       help="Writing tone (casual, reflective, humorous, serious)")
    gen_p.add_argument("--word-count", type=int, default=500,
                       help="Target word count for blog posts")
    gen_p.add_argument("--image-desc", default=None,
                       help="Description of the image (for Instagram context)")
    gen_p.add_argument("--image", default=None,
                       help="Path to image file (required for Instagram posting)")
    gen_p.add_argument("--post", action="store_true",
                       help="Actually post the generated content")

    # post
    post_p = subparsers.add_parser("post", help="Post pre-written content")
    post_p.add_argument("platform", choices=["blog", "twitter", "instagram"])
    post_p.add_argument("--content", required=True, help="Content to post")
    post_p.add_argument("--title", default=None, help="Title (for blog posts)")
    post_p.add_argument("--image", default=None, help="Image path (for Instagram)")

    # status
    subparsers.add_parser("status", help="Check model server and platform status")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "generate":
        asyncio.run(cmd_generate(args))
    elif args.command == "post":
        asyncio.run(cmd_post(args))
    elif args.command == "status":
        asyncio.run(cmd_status(args))


if __name__ == "__main__":
    main()
