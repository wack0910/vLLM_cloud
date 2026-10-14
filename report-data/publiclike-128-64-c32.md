# 짧은 입력·출력 실험 결과: 입력 목표 128 / 출력 목표 64 / 동시 요청 32

출처: 사용자가 대화에 공유한 콘솔 결과. 직전에 제시한 vLLM CLI를 실행한 것으로 해석하되,
실제 명령과 서버 설정은 원본 JSON/설정 사본으로 최종 확인한다.
Qwen 공식 벤치마크 재현 결과가 아니라 사용자 환경의 API 서빙 측정이다.

| 항목 | 값 |
|---|---:|
| Successful requests | 160 |
| Failed requests | 0 |
| Maximum request concurrency | 32 |
| Benchmark duration (s) | 38.74 |
| Total input tokens | 22450 |
| Total generated tokens | 10240 |
| Request throughput (req/s) | 4.13 |
| Output token throughput (tok/s) | 264.32 |
| Peak output token throughput (tok/s) | 366.00 |
| Peak concurrent requests | 48.00 |
| Total token throughput (tok/s) | 843.80 |

| 지표 | 평균 (ms) | 중앙값/p50 (ms) | p95 (ms) |
|---|---:|---:|---:|
| TTFT | 4350.17 | 4753.61 | 4857.49 |
| TPOT | 47.79 | 47.21 | 54.00 |
| ITL | 47.04 | 46.33 | 46.72 |
| E2EL | 7360.75 | 7728.13 | 7831.32 |

## 이전 부하와의 관측 비교

이전 입력 목표 1024 / 출력 목표 128 / c32 / 요청 160 결과는
측정 시간 124.79초, 출력 164.12tok/s, 평균 TTFT 13230.54ms,
평균 TPOT 84.24ms/token이었다.

- 이번 측정 시간은 약 69.0% 짧다.
- 전체 출력 처리량은 약 61.1% 높다.
- 평균 TTFT는 약 67.1% 낮다.
- 평균 TPOT는 약 43.3% 낮다.
- 입력 및 출력 길이를 모두 변경했으므로 서버 튜닝 효과로 해석하지 않는다.
- 평균 입력 140.3125 tokens/request, 평균 출력 64 tokens/request.

## 외부 L40S 사례와 비교

| 결과 | 이번 실험 | 외부 Interactive | 외부 Throughput |
|---|---:|---:|---:|
| 출력 tok/s | 264.32 | 318.6 | 354.9 |
| p95 TTFT(ms) | 4857.49 | 2511 | 1891 |
| p95 E2EL(ms) | 7831.32 | 6424 | 5768 |

원문에서 입력/출력 목표 128/64와 동시 요청 32를 확인했다.
단순 출력 처리량 수치 비율은 외부 Interactive 대비 83.0%, Throughput 대비 74.5%다.
이는 동등 조건으로 보정된 성능 달성률이 아니다.
외부는 AIPerf, vLLM 0.22.1, FP8 KV cache, Prefix Caching 활성화 조건이며
두 서버 프로필의 전체 설정과 당시 전체 CLI는 확인되지 않았다.
Random 입력 생성 방식, 캐시 적중, 생성 조건, 버전, 서버 배치 설정 차이가 남아 있다.

Peak output 366.00을 외부 평균 출력 처리량과 비교하지 않는다.
Peak concurrent requests 48.00을 순간 실제 동시 요청 수로 단정하지 않는다.
설치 버전의 집계 산식과 서버 running/waiting 지표를 대조해야 한다.

## 후속 실험에 적용할 때

짧은 탐색용 입력128/출력64/c32/요청160 조건을 채택하면 이 결과를 새 기준값으로 삼는다.
기존 입력1024/출력128 조건과는 다른 실험군으로 구분한다.
짧은 입력·출력에서 캐시 압박이 작으면 메모리 예산 변화가 처리량 차이로 드러나지 않을 수 있다.
각 서버 기동의 캐시 용량과 측정 중 캐시 사용률/대기/preemption 기록도 함께 사용한다.

출처: https://www.reddit.com/r/Qwen_AI/comments/1w0uc9i/benchmark_qwen3827bfp8_on_1_l40s_opencode_c1c8c32/
