# 공개 벤치마크와의 비교 확인

확인일: 2026-10-14. 사용자 제공 CLI 로그와 공개 1차 자료를 기준으로 정리했다.

## 사용자 최신 측정

- Qwen/Qwen3.8-27B-FP8, 기존 전달 환경 L40S 1장.
- 공식 vllm bench serve, openai-chat, random 입력 목표 1024 / 출력 목표 128.
- 요청 160개, 최대 동시 요청 32, request-rate inf, num-warmups 0,
  seed 0, temperature 0, ignore-eos true.
- CLI에 extra-body 및 chat-template-kwargs가 없으므로 thinking 비활성화 여부는
  실행 중인 서버의 default-chat-template-kwargs를 확인해야 한다.
- 성공 160 / 실패 0, 측정 124.79초, 출력 처리량 164.12tok/s.
- 평균 TTFT 13230.54ms, p95 TTFT 16926.78ms.
- 평균 TPOT 84.24ms/token, p95 TPOT 91.99ms/token.
- 평균 E2EL 23929.49ms, p95 E2EL 27332.00ms.

## 공식 발표 자료

Qwen 공식 모델 카드의 Benchmark Results는 GPQA, SWE-bench 등 능력 평가이며,
현재의 Random API 서빙 속도 측정과 다른 평가다.
확인한 모델 카드와 공식 vLLM recipe에서는 L40S 1장, FP8, 입력 1024/출력 128,
동시 요청 32에 대응하는 공식 TTFT/TPOT/처리량 기준을 찾지 못했다.
공식 recipe의 수치는 다른 가속기, 정밀도 또는 speculative decoding 조건이 포함되어 있다.
따라서 공식 발표 대비 성능 도달률이나 정상 속도 여부를 확정하지 않는다.

## 동일 모델·GPU의 외부 직접 측정 사례

InferCrane 개발자가 공개한 자체 실험이며 Qwen 공식 발표는 아니다.

| 조건 | 외부 실험 | 사용자 실험 |
|---|---|---|
| 모델 | Qwen/Qwen3.8-27B-FP8 | 동일 모델 ID |
| GPU | RunPod L40S 1장 | L40S 1장으로 전달받음 |
| 입력/출력 목표 | 128 / 64 | 1024 / 128 |
| 동시 요청 | 32 | 32 |
| 도구 | AIPerf | vLLM bench serve |
| vLLM 버전 | 0.22.1 | 미제공 |
| 문맥 상한 | 32768 | 실제 서버 설정 미제공 |
| KV cache dtype | FP8 | 실제 서버 설정 미제공 |
| Prefix Caching | 활성화 | 실제 서버 설정 미제공 |
| 출력 처리량 | Interactive 318.6, Throughput 354.9 tok/s | 164.12 tok/s |
| p95 TTFT | Interactive 2511, Throughput 1891ms | 16926.78ms |
| p95 E2EL | Interactive 6424, Throughput 5768ms | 27332.00ms |

외부 사례는 프로필당 1회, 짧은 출력으로 수행됐다고 작성자가 명시했다.
같은 GPU라도 부하·캐시·서버 설정·도구가 다르므로 위 수치로 속도 차이의 원인이나
사용자 환경의 이상 여부를 판정하지 않는다. 직접 비교에는 같은 조건으로 재측정해야 한다.

## 보고서용 결론

Qwen3.8-27B-FP8 공식 모델 카드의 능력 평가와 별도로, 본 실험은 L40S 단일 GPU에서
API 서빙 성능을 측정하였다. 입력 목표 1024토큰, 출력 목표 128토큰, 최대 동시 요청 32에서
출력 처리량 164.12tokens/s와 p95 TTFT 16926.78ms를 관측하였다.
동일 조건의 공식 속도 기준은 확인되지 않아 공식 성능 재현 여부는 판단하지 않았다.
동일 모델·GPU를 사용한 외부 측정은 조건 차이를 명시한 참고 자료로만 사용하였다.

## 출처

- Qwen 공식 모델 카드: https://huggingface.co/Qwen/Qwen3.8-27B-FP8
- 공식 vLLM recipe: https://recipes.vllm.ai/Qwen/Qwen3.8-27B
- 실험 수행자의 공개 게시물: https://www.reddit.com/r/Qwen_AI/comments/1w0uc9i/benchmark_qwen3827bfp8_on_1_l40s_opencode_c1c8c32/
