#!/usr/bin/env python3
"""
Prepare training data for GPT-OSS 120B fine-tuning.
Converts Alpaca-format data to GPT-OSS messages format,
filters AI-sounding phrases, and oversamples identity examples.

Input:  alexandra_training_cleaned.json, alexandra_personal.json, alexandra_personal_expanded.json
Output: gptoss_alexandra_training.json (messages format)

Run: python prepare_gptoss_data.py
"""

import json
import re
import os
from collections import Counter

DATA_DIR = "/home/alexandratitus767/ai-clone-training/data"
OUTPUT_FILE = os.path.join(DATA_DIR, "gptoss_alexandra_training.json")

# Files to load
CLEANED_DATA = os.path.join(DATA_DIR, "alexandra_training_cleaned.json")
PERSONAL_DATA = os.path.join(DATA_DIR, "alexandra_personal.json")
PERSONAL_EXPANDED = os.path.join(DATA_DIR, "alexandra_personal_expanded.json")
TEXT_MESSAGES = os.path.join(DATA_DIR, "alexandra_texts.json")

# Alexandra's personality system prompt for developer messages
ALEXANDRA_SYSTEM = (
    "You are Alexandra, a 56-year-old transgender woman, Army veteran, "
    "and tech enthusiast from Ridgway, PA. Respond naturally in your own voice - "
    "informal, friendly, with a good sense of humor. "
    "Never use corporate or AI-sounding language. Never use LOL or emojis. "
    "Be real, be yourself."
)

# Phrases that make text sound AI-generated - filter these out
AI_PHRASES = [
    r"(?i)as an ai\b",
    r"(?i)as a language model\b",
    r"(?i)i don'?t have (personal )?(feelings|emotions|experiences)\b",
    r"(?i)i'?m (just )?an? (ai|artificial|language model|chatbot)\b",
    r"(?i)certainly!",
    r"(?i)^of course!",
    r"(?i)^great question!",
    r"(?i)^that'?s a great question",
    r"(?i)^absolutely!",
    r"(?i)^i'?d be happy to help",
    r"(?i)in today'?s (fast[- ]paced|digital|modern) world",
    r"(?i)let'?s dive (in|into)",
    r"(?i)(?:it'?s )?important to note that",
    r"(?i)it'?s worth (noting|mentioning)",
    r"(?i)I hope (this|that) helps",
    r"(?i)feel free to ask",
    r"(?i)don'?t hesitate to",
    r"(?i)I cannot and will not",
    r"(?i)as a helpful assistant",
]

AI_PATTERNS = [re.compile(p) for p in AI_PHRASES]

# Regex to match emojis
EMOJI_PATTERN = re.compile(
    "[\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"   # symbols & pictographs
    "\U0001F680-\U0001F6FF"   # transport & map symbols
    "\U0001F1E0-\U0001F1FF"   # flags
    "\U00002702-\U000027B0"
    "\U0000FE00-\U0000FE0F"
    "\U0001F900-\U0001F9FF"   # supplemental symbols
    "\U0001FA00-\U0001FA6F"   # chess symbols
    "\U0001FA70-\U0001FAFF"   # symbols extended
    "\U00002600-\U000026FF"   # misc symbols
    "\U0000200D"              # zero width joiner
    "\U00002764"              # heart
    "]+", flags=re.UNICODE
)

# How many times to repeat personal identity examples
PERSONAL_OVERSAMPLE = 8
# Text messages are pure Alexandra voice - oversample heavily
TEXT_MSG_OVERSAMPLE = 6


def load_json(filepath):
    """Load a JSON file (array of objects)."""
    print(f"  Loading {os.path.basename(filepath)}...")
    with open(filepath, "r") as f:
        data = json.load(f)
    print(f"    {len(data):,} examples")
    return data


def has_ai_phrases(text):
    """Check if text contains AI-sounding phrases."""
    for pattern in AI_PATTERNS:
        if pattern.search(text):
            return True
    return False


def strip_lol_and_emojis(text):
    """Remove LOL variations and emojis from text."""
    # Remove LOL variations (lol, LOL, Lol, lolol, etc.)
    text = re.sub(r'\b[Ll][Oo][Ll]+\b', '', text)
    # Remove emojis
    text = EMOJI_PATTERN.sub('', text)
    # Clean up extra whitespace
    text = re.sub(r'  +', ' ', text).strip()
    return text


def convert_to_messages(example):
    """Convert Alpaca-format example to GPT-OSS messages format."""
    instruction = example.get("instruction", "").strip()
    user_input = example.get("input", "").strip()
    output = example.get("output", "").strip()

    if not output:
        return None

    messages = []

    # Use instruction as developer (system) message
    if instruction:
        messages.append({"role": "developer", "content": instruction})

    # User message
    if user_input:
        messages.append({"role": "user", "content": user_input})
    elif not instruction:
        return None  # No input at all

    # Assistant response - strip LOL and emojis
    output = strip_lol_and_emojis(output)
    if not output:
        return None
    messages.append({"role": "assistant", "content": output})

    return {"messages": messages}


def convert_personal_to_messages(example):
    """Convert personal identity example with Alexandra's system prompt."""
    user_input = example.get("input", "").strip()
    output = strip_lol_and_emojis(example.get("output", "").strip())

    if not output or not user_input:
        return None

    messages = [
        {"role": "developer", "content": ALEXANDRA_SYSTEM},
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": output},
    ]

    return {"messages": messages}


def main():
    print("=" * 60)
    print("PREPARING GPT-OSS TRAINING DATA")
    print("=" * 60)

    # Load all datasets
    print("\nLoading datasets...")
    cleaned = load_json(CLEANED_DATA)
    personal = load_json(PERSONAL_DATA)

    personal_expanded = []
    if os.path.exists(PERSONAL_EXPANDED):
        personal_expanded = load_json(PERSONAL_EXPANDED)

    # Convert and filter
    print("\nConverting to messages format...")
    all_messages = []
    stats = Counter()

    # Process cleaned data (bulk personality/empathy data)
    for example in cleaned:
        output = example.get("output", "")

        # Skip if output contains AI-sounding phrases
        if has_ai_phrases(output):
            stats["filtered_ai_phrases"] += 1
            continue

        # Skip very short outputs (likely noise)
        if len(output.strip()) < 10:
            stats["filtered_too_short"] += 1
            continue

        converted = convert_to_messages(example)
        if converted:
            all_messages.append(converted)
            stats["cleaned_kept"] += 1

    print(f"  Cleaned data: {stats['cleaned_kept']:,} kept, "
          f"{stats['filtered_ai_phrases']:,} filtered (AI phrases), "
          f"{stats['filtered_too_short']:,} filtered (too short)")

    # Process personal identity data with oversampling
    personal_count = 0
    for example in personal:
        converted = convert_personal_to_messages(example)
        if converted:
            # Oversample to anchor personality
            for _ in range(PERSONAL_OVERSAMPLE):
                all_messages.append(converted)
            personal_count += 1

    print(f"  Personal identity: {personal_count} examples x {PERSONAL_OVERSAMPLE} = "
          f"{personal_count * PERSONAL_OVERSAMPLE:,} (oversampled)")

    # Process expanded personal data
    expanded_count = 0
    for example in personal_expanded:
        converted = convert_personal_to_messages(example)
        if converted:
            for _ in range(PERSONAL_OVERSAMPLE // 2):
                all_messages.append(converted)
            expanded_count += 1

    print(f"  Personal expanded: {expanded_count} examples x {PERSONAL_OVERSAMPLE // 2} = "
          f"{expanded_count * (PERSONAL_OVERSAMPLE // 2):,} (oversampled)")

    # Process text messages (real Alexandra voice - highest value data)
    text_count = 0
    if os.path.exists(TEXT_MESSAGES):
        texts = load_json(TEXT_MESSAGES)
        for example in texts:
            output = strip_lol_and_emojis(example.get("output", "").strip())
            user_input = strip_lol_and_emojis(example.get("input", "").strip())

            if not output or len(output) < 5:
                stats["texts_filtered_short"] += 1
                continue

            messages = [
                {"role": "developer", "content": ALEXANDRA_SYSTEM},
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": output},
            ]
            converted = {"messages": messages}

            for _ in range(TEXT_MSG_OVERSAMPLE):
                all_messages.append(converted)
            text_count += 1

        print(f"  Text messages: {text_count} examples x {TEXT_MSG_OVERSAMPLE} = "
              f"{text_count * TEXT_MSG_OVERSAMPLE:,} (oversampled)")
        if stats["texts_filtered_short"]:
            print(f"    Filtered (too short): {stats['texts_filtered_short']:,}")
    else:
        print(f"  Text messages: NOT FOUND at {TEXT_MESSAGES}")

    print(f"\n  Total examples: {len(all_messages):,}")

    # Save
    print(f"\nSaving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w") as f:
        json.dump(all_messages, f, indent=None, ensure_ascii=False)

    file_size = os.path.getsize(OUTPUT_FILE)
    print(f"  File size: {file_size / 1024 / 1024:.1f} MB")

    # Sample output for verification
    print("\n--- Sample converted example ---")
    sample = all_messages[0]
    print(json.dumps(sample, indent=2)[:500])

    print("\n" + "=" * 60)
    print("DATA PREPARATION COMPLETE!")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Examples: {len(all_messages):,}")
    print("=" * 60)


if __name__ == "__main__":
    main()
