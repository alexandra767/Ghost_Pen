#!/usr/bin/env python3
"""
Fine-tune GPT-OSS 120B with Alexandra's personality data using QLoRA + Unsloth.
Designed for NVIDIA DGX Spark (128GB unified memory).

Memory: ~65GB QLoRA on 128GB unified = comfortable fit.

Prerequisites:
  1. Run download_gptoss.py to download the model
  2. Run prepare_gptoss_data.py to prepare training data
  3. Run inside Unsloth Docker container (see dgx-spark-playbooks/nvidia/unsloth/)

Run: python train_gptoss_alexandra.py
"""

import os
import torch
from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template, standardize_sharegpt
from datasets import load_dataset
from trl import SFTTrainer, SFTConfig

# === Paths ===
MODEL_NAME = "unsloth/gpt-oss-120b-bnb-4bit"
# If downloaded locally, use:
# MODEL_NAME = "/home/alexandratitus767/models/gpt-oss-120b"

TRAINING_DATA = "/home/alexandratitus767/ai-clone-training/data/gptoss_alexandra_training.json"
OUTPUT_DIR = "/home/alexandratitus767/ai-clone-training/gptoss-alexandra-lora"

# === Hyperparameters ===
MAX_SEQ_LENGTH = 4096
LORA_RANK = 32
LORA_ALPHA = 64
BATCH_SIZE = 1
GRAD_ACCUM = 16
LEARNING_RATE = 1e-4
NUM_EPOCHS = 2
WARMUP_STEPS = 100
SAVE_STEPS = 500

print("=" * 60)
print("GPT-OSS 120B PERSONALITY FINE-TUNING")
print("=" * 60)

# Check training data exists
if not os.path.exists(TRAINING_DATA):
    print(f"ERROR: Training data not found at {TRAINING_DATA}")
    print("Run prepare_gptoss_data.py first!")
    exit(1)

# Flush memory caches (DGX Spark unified memory optimization)
print("\nFlushing memory caches...")
try:
    os.system("sync; echo 3 > /proc/sys/vm/drop_caches 2>/dev/null")
except Exception:
    pass

# === Load Model ===
print(f"\nLoading {MODEL_NAME}...")
print("  This may take several minutes for 120B model...")

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=MODEL_NAME,
    max_seq_length=MAX_SEQ_LENGTH,
    load_in_4bit=True,
    dtype=torch.bfloat16,
)

# Apply the GPT-OSS chat template
tokenizer = get_chat_template(tokenizer, chat_template="gpt-oss")

print(f"  Model loaded successfully")
print(f"  Max sequence length: {MAX_SEQ_LENGTH}")

# === Add LoRA Adapters ===
print(f"\nAdding LoRA adapters (rank={LORA_RANK}, alpha={LORA_ALPHA})...")

model = FastLanguageModel.get_peft_model(
    model,
    r=LORA_RANK,
    lora_alpha=LORA_ALPHA,
    lora_dropout=0,
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    use_gradient_checkpointing="unsloth",
    random_state=3407,
    use_rslora=False,
    bias="none",
    max_seq_length=MAX_SEQ_LENGTH,
)

model.print_trainable_parameters()

# === Load Dataset ===
print(f"\nLoading training data from {TRAINING_DATA}...")

dataset = load_dataset("json", data_files=TRAINING_DATA, split="train")
print(f"  Loaded {len(dataset):,} examples")

# Standardize to ShareGPT format for Unsloth
dataset = standardize_sharegpt(dataset)

# Apply chat template to format conversations
def formatting_func(examples):
    convos = examples["messages"]
    texts = [
        tokenizer.apply_chat_template(
            convo, tokenize=False, add_generation_prompt=False
        )
        for convo in convos
    ]
    return {"text": texts}

dataset = dataset.map(formatting_func, batched=True)
dataset = dataset.shuffle(seed=42)

# Filter very short examples
dataset = dataset.filter(lambda x: len(x["text"]) > 50)
print(f"  After filtering: {len(dataset):,} examples")

# === Training ===
effective_batch = BATCH_SIZE * GRAD_ACCUM
total_steps = (len(dataset) * NUM_EPOCHS) // effective_batch

print(f"\n{'=' * 60}")
print("TRAINING CONFIGURATION")
print(f"  Model: GPT-OSS 120B (QLoRA 4-bit)")
print(f"  LoRA: rank={LORA_RANK}, alpha={LORA_ALPHA}")
print(f"  Examples: {len(dataset):,}")
print(f"  Epochs: {NUM_EPOCHS}")
print(f"  Batch: {BATCH_SIZE} x {GRAD_ACCUM} = {effective_batch}")
print(f"  Learning rate: {LEARNING_RATE}")
print(f"  Estimated steps: ~{total_steps:,}")
print(f"  Checkpoints every: {SAVE_STEPS} steps")
print(f"  Output: {OUTPUT_DIR}")
print(f"{'=' * 60}\n")

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    args=SFTConfig(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUM,
        num_train_epochs=NUM_EPOCHS,
        learning_rate=LEARNING_RATE,
        warmup_steps=WARMUP_STEPS,
        logging_steps=25,
        save_steps=SAVE_STEPS,
        save_total_limit=3,
        max_seq_length=MAX_SEQ_LENGTH,
        dataset_text_field="text",
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        seed=3407,
        bf16=True,
        report_to="none",
        packing=False,
    ),
)

print("Starting training...")
trainer.train()

# === Save Final ===
final_path = OUTPUT_DIR + "-final"
print(f"\nSaving final LoRA to {final_path}...")
model.save_pretrained(final_path)
tokenizer.save_pretrained(final_path)

# Also save merged model for vLLM serving
merged_path = "/home/alexandratitus767/models/gptoss-alexandra-merged"
print(f"\nMerging LoRA and saving full model to {merged_path}...")
print("  (This creates a standalone model for vLLM inference)")
try:
    model.save_pretrained_merged(
        merged_path,
        tokenizer,
        save_method="merged_16bit",
    )
    print(f"  Merged model saved to: {merged_path}")
except Exception as e:
    print(f"  Merge failed (can be done later): {e}")
    print(f"  LoRA adapter saved to: {final_path}")
    print(f"  Run merge_lora.py later if needed")

print("\n" + "=" * 60)
print("TRAINING COMPLETE!")
print(f"  LoRA adapter: {final_path}")
print(f"  Merged model: {merged_path}")
print("=" * 60)
