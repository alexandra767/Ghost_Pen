#!/usr/bin/env python3
"""
Download GPT-OSS 120B (pre-quantized Unsloth variant) for fine-tuning.
Uses HuggingFace Hub with fast transfer for optimal download speed.

Run: python download_gptoss.py
"""

import os
import sys

# Enable fast transfer
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"

from huggingface_hub import snapshot_download

MODEL_REPO = "unsloth/gpt-oss-120b-bnb-4bit"
LOCAL_DIR = "/home/alexandratitus767/models/gpt-oss-120b"

def main():
    print("=" * 60)
    print("DOWNLOADING GPT-OSS 120B (Unsloth 4-bit)")
    print(f"  From: {MODEL_REPO}")
    print(f"  To:   {LOCAL_DIR}")
    print("=" * 60)

    # Check if already downloaded
    if os.path.exists(LOCAL_DIR) and any(
        f.endswith(".safetensors") for f in os.listdir(LOCAL_DIR)
    ):
        print("\nModel files already exist. To re-download, remove the directory first.")
        print(f"  rm -rf {LOCAL_DIR}")
        sys.exit(0)

    os.makedirs(LOCAL_DIR, exist_ok=True)

    print("\nStarting download (this may take a while)...")
    snapshot_download(
        repo_id=MODEL_REPO,
        local_dir=LOCAL_DIR,
        resume_download=True,
    )

    print("\n" + "=" * 60)
    print("DOWNLOAD COMPLETE!")
    print(f"Model saved to: {LOCAL_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
