# 빠른 탐색 기준 결과 — 동시 요청 한도 32

출처: 사용자가 대화에 붙여넣은 Serving Benchmark Result. 원본 JSON과 실제 실행 명령/서버 설정은 추후 대조한다.
이 파일은 Word 보고서 작성용 자료이며, 서버 튜닝의 인과적 효과나 최적 설정을 확정하지 않는다.

## 일반 결과

| 항목 | 값 |
|---|---:|
| Successful requests | 160 |
| Failed requests | 0 |
| Maximum request concurrency | 32 |
| Benchmark duration (s) | 124.84 |
| Total input tokens | 165823 |
| Total generated tokens | 20480 |
| Request throughput (req/s) | 1.28 |
| Output token throughput (tok/s) | 164.05 |
| Peak output token throughput (tok/s) | 337.00 |
| Peak concurrent requests | 36.00 |
| Total token throughput (tok/s) | 1492.29 |

| 지표 | 평균 (ms) | 중앙값 (ms) | p50 (ms) | p95 (ms) |
|---|---:|---:|---:|---:|
| TTFT | 13237.97 | 13786.32 | 13786.32 | 16947.58 |
| TPOT | 84.27 | 83.65 | 83.65 | 92.09 |
| ITL | 83.61 | 47.71 | 47.71 | 441.40 |
| E2EL | 23940.18 | 24906.07 | 24906.07 | 27360.35 |

## 해석

- 160/160 요청 성공. 단기 관측 성공률 100%이며 장시간 안정성 보장은 아니다.
- 평균 입력 165823/160 = 1036.39375 tokens/request, 평균 출력 20480/160 = 128 tokens/request.
- 평균 첫 출력 대기는 약 13.24초, 평균 전체 응답 시간은 약 23.94초.
- 요청당 평균 decode 속도 근사치 1000/84.27 = 약 11.87 tokens/s. 전체 출력 처리량 164.05 tokens/s와 다른 값이다.
- 160/124.84 ≈ 1.28 req/s, 20480/124.84 ≈ 164.05 output tok/s.
- 출력 길이가 128로 고정된 요청들의 평균값에서는 (23940.18 - 13237.97)/127 ≈ 84.27ms/token이 성립한다.
- ITL 중앙값 47.71ms, p95 441.40ms로 간격 분포의 긴 꼬리를 확인할 수 있다. 원인 진단에는 서버 대기·실행 요청 및 캐시 지표가 필요하다.
- 최초 c4 기준의 3회 평균 출력 처리량 72.5167 tok/s 대비 약 2.26배의 출력 처리량이 관측되었다.
  동시에 평균 TTFT는 1.067초에서 13.238초로, 평균 TPOT는 47.187에서 84.27ms/token으로 증가했다.
  요청 개수 1000→160과 동시 요청 한도 4→32가 함께 바뀌었으므로 통제된 서버 튜닝 비교로 취급하지 않는다.
- 이번 결과를 이후 동일한 160개·c32·입출력 조건의 서버 설정 비교 기준으로 사용한다.
- KV Cache 용량과 사용률은 본 콘솔 결과에 없으며 아직 제공되지 않았다.

## Peak concurrent requests 해석 근거

공식 v0.17.0 소스는 요청 시작부터 완료까지 걸친 각 1초 버킷에 요청을 누적한다.
같은 1초 안에 끝난 요청과 새로 시작한 요청을 함께 세므로, 버킷 최대값이 클라이언트
동시 요청 한도를 넘을 수 있다. 따라서 36을 실제 순간 동시 실행 요청 수로 단정하지 않는다.
사용자 설치 버전은 아직 확인되지 않았으므로 해당 버전의 소스로 산식을 최종 대조한다.

근거: https://github.com/vllm-project/vllm/blob/v0.17.0/vllm/benchmarks/serve.py

## 도구 출처

공식 도구는 `vllm bench serve`다. 이 작업 공간의 `run_bench.py`는 Codex가 작성한
YAML→CLI 실행 보조 파일이며 공식 배포 스크립트가 아니다. `bench.yaml`과 `bench-fast.yaml`도
이번 실험용으로 작성한 설정이다. 앞으로 설명과 실행은 공식 CLI를 기준으로 진행한다.
