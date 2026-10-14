#!/usr/bin/env bash
# 이번 과제용 셸 파일: 측정은 공식 vllm bench serve가 수행합니다.
set -euo pipefail
mkdir -p results/seq32-r3072-o256-c32
vllm bench serve \
  --backend openai-chat \
  --base-url http://127.0.0.1:8000 \
  --model Qwen/Qwen3.8-27B-FP8 \
  --endpoint /v1/chat/completions \
  --dataset-name random \
  --random-input-len 3072 \
  --random-output-len 256 \
  --random-range-ratio 0 \
  --random-prefix-len 0 \
  --num-prompts 100 \
  --num-warmups 0 \
  --request-rate inf \
  --max-concurrency 32 \
  --seed 0 \
  --temperature 0 \
  --ignore-eos \
  --extra-body '{"chat_template_kwargs":{"enable_thinking":false}}' \
  --percentile-metrics ttft,tpot,itl,e2el \
  --metric-percentiles 50,95 \
  --save-result \
  --save-detailed \
  --result-dir results/seq32-r3072-o256-c32 \
  --result-filename benchmark.json \
  --label seq32-r3072-o256-c32 \
  --plot-timeline \
  --timeline-itl-thresholds 50,100 \
  --plot-dataset-stats \
  2>&1 | tee results/seq32-r3072-o256-c32/console.log
