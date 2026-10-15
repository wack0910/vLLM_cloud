import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from llmcompressor import oneshot
from llmcompressor.modifiers.quantization import QuantizationModifier

BASE = Path("/root/workspace/quantization")
MODEL_DIR = BASE / "models/Qwen2.5-7B-Instruct"
OUTPUT_DIR = BASE / "outputs/Qwen2.5-7B-FP8-oneshot"
LOG_DIR = BASE / "logs/llmcompressor_fp8"

if not MODEL_DIR.is_dir():
    raise FileNotFoundError(MODEL_DIR)

# 기존 결과를 실수로 덮어쓰지 않도록 보호
if OUTPUT_DIR.exists():
    raise FileExistsError(OUTPUT_DIR)

LOG_DIR.mkdir(parents=True, exist_ok=True)

start = time.perf_counter()

# 1. BF16 원본 모델을 GPU에 로드
model = AutoModelForCausalLM.from_pretrained(
    str(MODEL_DIR),
    torch_dtype=torch.bfloat16,
    device_map="cuda:0",
    low_cpu_mem_usage=True,
)

tokenizer = AutoTokenizer.from_pretrained(
    str(MODEL_DIR)
)

print("Original dtype:", model.dtype, flush=True)
print("Original device:", model.device, flush=True)

# 2. FP8 양자화 설정
recipe = QuantizationModifier(
    targets="Linear",
    scheme="FP8_DYNAMIC",
    ignore=[
        "lm_head",
        "model.embed_tokens",
    ],
)

print("Quantization scheme: FP8_DYNAMIC", flush=True)
print("Target layers: Linear", flush=True)
print("Calibration: None", flush=True)

# 3. 양자화 및 결과 저장
oneshot(
    model=model,
    tokenizer=tokenizer,
    recipe=recipe,
    output_dir=str(OUTPUT_DIR),
    log_dir=str(LOG_DIR),
)

if torch.cuda.is_available():
    torch.cuda.synchronize()
    print(
        "PyTorch allocated peak MiB:",
        round(torch.cuda.max_memory_allocated() / 1024**2, 2),
        flush=True,
    )
    print(
        "PyTorch reserved peak MiB:",
        round(torch.cuda.max_memory_reserved() / 1024**2, 2),
        flush=True,
    )

elapsed = time.perf_counter() - start

print("Output directory:", OUTPUT_DIR, flush=True)
print("Elapsed seconds:", round(elapsed, 2), flush=True)
print("FP8 quantization completed", flush=True)
