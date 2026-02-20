#!/bin/bash
# Serve fine-tuned GPT-OSS Alexandra model via vLLM
# Provides OpenAI-compatible API at http://localhost:8000/v1/chat/completions

MERGED_MODEL="/home/alexandratitus767/models/gptoss-alexandra-merged"
LORA_PATH="/home/alexandratitus767/ai-clone-training/gptoss-alexandra-lora-final"
BASE_MODEL="unsloth/gpt-oss-120b-bnb-4bit"

echo "=================================================="
echo "SERVING GPT-OSS ALEXANDRA MODEL"
echo "=================================================="

# Option 1: Serve merged model (preferred - faster startup)
if [ -d "$MERGED_MODEL" ]; then
    echo "Serving merged model from: $MERGED_MODEL"
    echo "API: http://localhost:8000/v1/chat/completions"
    echo "=================================================="

    vllm serve "$MERGED_MODEL" \
        --host 0.0.0.0 \
        --port 8000 \
        --max-model-len 16384 \
        --gpu-memory-utilization 0.85 \
        --dtype auto \
        --served-model-name alexandra

# Option 2: Serve base model + LoRA adapter
elif [ -d "$LORA_PATH" ]; then
    echo "Merged model not found. Serving base + LoRA adapter."
    echo "Base:  $BASE_MODEL"
    echo "LoRA:  $LORA_PATH"
    echo "API: http://localhost:8000/v1/chat/completions"
    echo "=================================================="

    vllm serve "$BASE_MODEL" \
        --host 0.0.0.0 \
        --port 8000 \
        --max-model-len 16384 \
        --gpu-memory-utilization 0.85 \
        --dtype auto \
        --enable-lora \
        --lora-modules "alexandra=$LORA_PATH" \
        --served-model-name alexandra

else
    echo "ERROR: No model found!"
    echo "  Expected merged model at: $MERGED_MODEL"
    echo "  Or LoRA adapter at: $LORA_PATH"
    echo ""
    echo "Run training first: python train_gptoss_alexandra.py"
    exit 1
fi
