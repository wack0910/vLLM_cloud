#!/usr/bin/env bash
# 이 파일은 이번 과제용 명령 모음입니다. 측정은 공식 vllm bench serve가 수행합니다.
set -euo pipefail
RUN_ID="${1:?Usage: bash experiments-cache/bench-kv.sh kv-base}"
if [[ ! "$RUN_ID" =~ ^[A-Za-z0-9_-]+$ ]]; then
    echo 'RUN_ID must use letters, numbers, underscores, or hyphens.' >&2
    exit 2
fi
mkdir -p "results/$RUN_ID"
vllm bench serve \
  --backend openai-chat \
  --base-url http://127.0.0.1:8000 \
  --model Qwen/Qwen3.8-27B-FP8 \
  --endpoint /v1/chat/completions \
  --dataset-name random \
  --random-input-len 6144 \
  --random-output-len 256 \
  --random-range-ratio 0 \
  --random-prefix-len 0 \
  --num-prompts 100 \
  --num-warmups 0 \
  --request-rate inf \
  --max-concurrency 32 \
  --seed 17 \
  --temperature 0 \
  --ignore-eos \
  --extra-body '{"chat_template_kwargs":{"enable_thinking":false}}' \
  --percentile-metrics ttft,tpot,itl,e2el \
  --metric-percentiles 50,95 \
  --save-result \
  --save-detailed \
  --result-dir "results/$RUN_ID" \
  --result-filename benchmark.json \
  --label "$RUN_ID" \
  --plot-timeline \
  --timeline-itl-thresholds 50,100 \
  --plot-dataset-stats \
  2>&1 | tee "results/$RUN_ID/console.log"
