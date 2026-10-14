# vLLM 벤치마크 · 클라우드 인계

Qwen/Qwen3.8-27B-FP8를 L40S 1장에서 서비스하고, 설정별 지연·처리량을 비교하는 입문 과제입니다.
최종 결과물은 실제 측정값과 그래프를 포함한 간략한 Word 보고서입니다.

## 현재 상태 — 2026-10-14

- **완료:** B0, 서버 `max-num-seqs=16`, random 입력3072/출력256, 클라이언트 동시성32, 요청100개.
- **진행 중:** 서버 `max-num-seqs`만32로 변경하여 동일 부하 측정. 결과 아직 미수령.
- Prefix Caching 및 나머지 튜닝 실험은 아직 실행하지 않았습니다.
- 서버 로그 파일 제출은 사용자가 원하지 않습니다. 다시 필수 요구하지 마세요.

## 클라우드 작업 시작

1. 이 저장소를 작업 환경에 연결합니다.
2. [CLOUD_PROMPT.md](CLOUD_PROMPT.md) 내용을 새 작업의 첫 프롬프트로 붙여 넣습니다.
3. 에이전트는 [AGENTS.md](AGENTS.md)를 먼저 읽습니다.
4. seq32 결과가 제공되면 B0와 비교하고 그래프를 추가합니다.

클라우드 분석 환경에 L40S나 원격 서버 접속이 있다고 가정하지 않습니다.
사용자는 기존 GPU 서버에서 벤치마크를 실행하고 결과를 제공합니다.

## 주요 파일

| 파일 | 역할 |
|---|---|
| AGENTS.md | 확정 상태, 사용자 선호, 실험 통제 및 해석 원칙 |
| CLOUD_PROMPT.md | 새 클라우드 작업에 입력할 인계 프롬프트 |
| config/config-base.yaml | 완료된 B0 서버 설정: seq16 |
| config/config.yaml | 현재 진행 중인 서버 설정: seq32 |
| bench/seq32.sh | 현재 실행 중인 공식 벤치마크 CLI를 보관한 셸 파일 |
| report-data/base-r3072-o256-c32/ | B0 원본 JSON·콘솔·요청별 CSV·그래프 |
| report-data/plot_benchmark.py | 공식 JSON에서 보고서 그래프를 만드는 과제용 코드 |
| experiments-cache/collect_metrics.py | 공식 /metrics를 CSV로 저장하는 과제용 보조 코드 |
| experiments-cache/ | 이전에 제안한 장문 캐시 실험 계획. 아직 미실행 |
| docs/legacy-setup.md | 초기 설정/YAML 보조 도구 안내, 현재 실행 절차와 구분 |

루트 config.yaml은 초기 seq16 설정의 보존본입니다. 현재 서버 실행 경로는 config/config.yaml입니다.
run_bench.py와 bench*.yaml은 이전에 작성한 비공식 YAML 실행 보조 자료이며 현재 실험에서는 쓰지 않습니다.

## 기준값 B0

성공100 / 실패0, 소요207.04초, 출력 처리량123.64 token/s.

| 지표 | 평균 | P50 | P95 |
|---|---:|---:|---:|
| TTFT (s) | 32.140 | 34.785 | 46.514 |
| TPOT (ms) | 109.268 | 113.816 | 117.846 |
| ITL (ms) | 108.841 | 50.773 | 818.578 |
| E2EL (s) | 60.003 | 63.809 | 75.534 |

![기준 그래프](report-data/base-r3072-o256-c32/baseline-summary.png)

## 실행과 그래프

GPU 서버에서만:

```bash
vllm serve --config config/config.yaml
# 다른 세션; 이미 진행 중인 실행을 중복 시작하지 마세요.
bash bench/seq32.sh
```

GPU 없이 JSON 그래프 생성:

```bash
python -m pip install -r requirements-report.txt
python report-data/plot_benchmark.py \
  report-data/base-r3072-o256-c32/benchmark.json \
  report-data/base-r3072-o256-c32
```

한국어 폰트가 있으면 자동 사용하고, 없으면 그래프는 영어 라벨로 생성합니다.
Word 본문은 한국어로 작성합니다. 결과 JSON·CSV는 측정 원본으로 보존합니다.
