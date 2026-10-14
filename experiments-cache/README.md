# L40S / Qwen3.8-27B-FP8: 캐시 관찰 실험

작성일: 2026-10-14. 측정 요청은 조건별 100개로 유지합니다.
차이를 관찰하기 좋은 합성 부하이며, 실제 서비스의 평균 성능을 대표하지 않습니다.
성능 차이나 기동 성공은 원격 L40S에서 아직 검증하지 않았습니다.

## 출처와 파일

- 측정 도구: 공식 `vllm bench serve`.
- YAML: 이번 과제용 설정. 공식 기본값 전체 목록이 아닙니다.
- `bench-prefix.sh`, `bench-kv.sh`: 공식 CLI 명령을 적어 둔 Bash 파일입니다.
  별도 벤치마크 측정 로직이나 YAML 실행 보조 도구를 쓰지 않습니다.
- `collect_metrics.py`: 이번에 작성한 모니터링 보조 도구입니다. 공식 도구가 아닙니다.
  공식 `/metrics` 응답을 Python 표준 라이브러리로 CSV에 기록합니다.
  TTFT/TPOT/Throughput을 계산하지 않습니다.
- 기존 작업 폴더의 config.yaml/bench.yaml은 수정하지 않았습니다.

이 폴더를 Linux 작업 폴더의 `experiments-cache/`로 복사하고,
그 상위 작업 폴더에서 아래 명령을 실행합니다. 각 결과 폴더는 새 이름을 사용하세요.

## 실험 설계

| 실험 | 입력 목표 | 출력 목표 | 동시 요청 | 서버 변경 | 우선 볼 지표 |
|---|---|---|---:|---|---|
| Prefix | 같은 접두사 6144 + 서로 다른 뒤쪽 128 | 128 | 4 | Prefix OFF/ON | TTFT, 적중률, prefill, 처리량 |
| KV | 서로 다른 입력 6144 | 256 | 32 | 메모리 예산/시퀀스 한도 | KV 사용률, 대기, preemption, TTFT/TPOT |

입력 목표는 토크나이저와 채팅 템플릿 처리 후 실제 토큰 수와 다를 수 있습니다.
각 결과의 실제 토큰 수, 실패 여부, 서버가 반환한 길이를 확인합니다.
문맥 상한은 8192로 두어 목표 입력+출력에 여유를 둡니다.
`--ignore-eos`로 조기 종료를 억제하고 thinking을 끕니다.
질문/출력은 성능 실험용이며 의미나 답변 품질을 평가하지 않습니다.

Prefix 실험에서는 긴 입력과 짧은 출력을 사용합니다. 출력만 길게 하면 decode 비중이
커져서 prefill을 줄이는 Prefix Caching 효과가 가려질 수 있습니다.
동시성 4는 선행 요청의 계산 결과를 후속 요청이 재사용할 기회를 주기 위한 값입니다.
접두사는 한 종류로 반복해 효과가 나타나기 유리한 조건을 만듭니다.
일반 ShareGPT 성능 개선율로 일반화하지 않습니다.

## 준비

서버가 사용 중인 가상환경에서 다음을 실행합니다. 설치 버전을 고정해 extras를 추가합니다.

```bash
source /root/workspace/vllm-env/bin/activate
VLLM_VERSION=$(python -c 'from importlib.metadata import version; print(version("vllm"))')
python -m pip install "vllm[bench]==${VLLM_VERSION}"
vllm --version
nvidia-smi
```

설치 버전에 prefix_repetition 옵션이 있는지는 `vllm bench serve --help`로 확인합니다.
첨부해 준 기존 Namespace에는 해당 옵션들이 있었습니다.
그래프 의존성 오류가 남으면 로그를 보존하세요. JSON/CSV만 있어도 보고서 그래프를 만들 수 있습니다.

## 첫 실행: Prefix OFF

기존 서버를 종료하고 새 설정으로 시작합니다. 서버를 여러 개 동시에 띄우지 마세요.

터미널 A:

```bash
mkdir -p results/prefix-off
cp experiments-cache/config-base.yaml results/prefix-off/server-config.yaml
vllm serve --config experiments-cache/config-base.yaml 2>&1 | tee results/prefix-off/server.log
```

서버 준비 완료 후 터미널 C에서 모니터링을 먼저 시작하고 `First sample saved`를 확인합니다.

```bash
python experiments-cache/collect_metrics.py --out results/prefix-off/metrics.csv
```

터미널 B에서 측정:

```bash
bash experiments-cache/bench-prefix.sh prefix-off
```

측정 완료 후 2~3초 기다렸다가 터미널 C에서 Ctrl+C로 모니터링만 종료합니다.
서버 로그의 캐시 용량과 CSV 수집 성공 여부도 확인합니다.

## 두 번째 실행: Prefix ON

터미널 A의 서버를 종료한 후 시작합니다.

```bash
mkdir -p results/prefix-on
cp experiments-cache/config-prefix-on.yaml results/prefix-on/server-config.yaml
vllm serve --config experiments-cache/config-prefix-on.yaml 2>&1 | tee results/prefix-on/server.log
```

터미널 C와 B에서 각각:

```bash
python experiments-cache/collect_metrics.py --out results/prefix-on/metrics.csv
```

```bash
bash experiments-cache/bench-prefix.sh prefix-on
```

끝나면 같은 방식으로 모니터링을 종료합니다.
두 조건의 부하 명령은 결과 이름 외에는 동일합니다.
ON에서 prefix_hits_tokens_total 증가를 반드시 확인합니다. 적중이 없다면 큰 측정을
반복하지 말고 버전/서버 로그를 확인합니다. 하이브리드 모델은 상태 캐싱과 블록 경계가
관련되므로 접두사 전체가 반드시 재사용되는 것은 아닙니다.

주의: `num-warmups=0`이어도 공식 CLI의 사전 단일 요청 테스트가 있습니다.
ON에서는 이 요청이 공통 접두사를 미리 캐시할 수 있습니다. 따라서 이 결과는
"캐시 재사용이 가능한 반복 문맥 부하"이며 "첫 요청부터 완전히 cold인 서비스"가 아닙니다.
CSV의 모니터링 구간에는 사전 테스트와 측정 전후의 짧은 유휴 시간이 포함됩니다.
서버 재시작으로 이전 실험의 캐시와 누적 카운터를 초기화합니다.

## KV 실험: 같은 부하에 서버 옵션 하나만 변경

Prefix 실험과 별도 부하입니다. 다음 표의 모든 KV 실행에는 `bench-kv.sh`를 사용합니다.
매 실행 서버를 재시작하고, 모니터링을 먼저 켜고, 결과 폴더 이름을 일치시킵니다.

| 실행 ID | base 설정에 추가할 서버 CLI 옵션 | 비교 목적 |
|---|---|---|
| kv-base | 없음 | 0.90 / seq32 / len8192 기준 |
| kv-mem80 | --gpu-memory-utilization 0.80 | 캐시 공간이 줄 때의 영향 |
| kv-seq8 | --max-num-seqs 8 | 서버 동시 처리 한도의 영향 |
| kv-len16384 (선택) | --max-model-len 16384 | 요청 길이를 유지한 채 상한만 변경 |

예: 기준 실행, 터미널 A:

```bash
mkdir -p results/kv-base
cp experiments-cache/config-base.yaml results/kv-base/server-config.yaml
vllm serve --config experiments-cache/config-base.yaml 2>&1 | tee results/kv-base/server.log
```

터미널 C, B:

```bash
python experiments-cache/collect_metrics.py --out results/kv-base/metrics.csv
```

```bash
bash experiments-cache/bench-kv.sh kv-base
```

예: 메모리 예산 0.80 실행, 서버를 종료한 뒤 터미널 A:

```bash
mkdir -p results/kv-mem80
cp experiments-cache/config-base.yaml results/kv-mem80/server-config.yaml
printf '%s\n' '--gpu-memory-utilization 0.80' > results/kv-mem80/server-overrides.txt
vllm serve --config experiments-cache/config-base.yaml --gpu-memory-utilization 0.80 2>&1 | tee results/kv-mem80/server.log
```

터미널 C, B:

```bash
python experiments-cache/collect_metrics.py --out results/kv-mem80/metrics.csv
```

```bash
bash experiments-cache/bench-kv.sh kv-mem80
```

seq8/len16384도 표의 옵션과 실행 ID로 같은 순서를 따릅니다.
CLI 덮어쓰기 값도 파일에 기록하고 서버 시작 로그의 실제 설정을 확인하세요.

0.80에서 기동이 실패하면 실패 자체를 기록합니다. 기동 실패는 벤치마크 0점이 아닙니다.
필요하면 0.85 조건을 새 실행 ID로 추가하되, 길이/동시성은 유지하세요.
8192 기동 자체가 실패하면 먼저 로그를 확인합니다. 임의로 한 조건만 입력 길이를 낮추지 않습니다.

첫 KV 기준 결과에서 캐시가 충분하고 대기/preemption도 없다면 메모리 예산 차이가
거의 안 보일 수 있습니다. 이는 유효한 결과입니다. 필요할 때만 별도 12K 입력 실험을
설계하고, 비교 조건 전체의 문맥 상한과 입력 길이를 함께 고정합니다.
오래 실행하는 것만으로 KV 부족이 생기는 것은 아닙니다.

max-model-len은 실제 입력 길이가 아닙니다. 8192 -> 16384라고 캐시 사용량이 두 배가
되거나 속도가 반드시 느려지는 것은 아닙니다. 시작 로그의 실제 캐시 용량을 비교합니다.
Qwen3.8은 하이브리드 모델이므로 full-attention KV 외의 상태 메모리도 영향을 줍니다.

## CSV와 그래프 해석

- kv_cache_usage_pct: 1초 간격 샘플. 0~100%. 여러 엔진이면 최대값.
- requests_running / requests_waiting: 합계.
- preemptions_total: 누적 카운터. 마지막-처음의 증가량을 사용합니다.
- prefix_hits_tokens_total / prefix_queries_tokens_total: 누적 토큰 카운터.
- 적중률 = 100 * (마지막 hits - 처음 hits) / (마지막 queries - 처음 queries).
  분모가 0이면 N/A입니다. 요청 수 기준 적중률이 아닙니다.
- 없는 지표는 공란이고 수집 실패는 fetch_ok=0입니다. 이를 0% 사용/적중으로 해석하지 않습니다.
- metrics.start.prom / metrics.end.prom: 첫/마지막 성공 응답 원본.
- 1초 샘플 최대값은 순간 최대값과 다릅니다. 수집 시간은 interval에 HTTP 시간이 추가됩니다.
- 캐시 사용률은 용량 대비 비율입니다. 서로 다른 설정은 캐시 총용량도 함께 봅니다.
  Prefix ON에서 사용률이 높게 남아도 재사용 가능한 캐시일 수 있습니다.

공식 옵션이 만드는 그래프:

- --plot-timeline: 브라우저에서 볼 수 있는 HTML 타임라인.
- --plot-dataset-stats: 입력/출력 길이 분포 그래프.
- --timeline-itl-thresholds 50,100: 타임라인 색 경계, 단위 ms. 서비스 합격 기준이 아닙니다.
- --save-result --save-detailed: 요약/요청별 지연을 JSON에 저장.

보고서에서는 JSON/CSV로 다음 정적 PNG 그래프를 만들고 Word에 넣습니다.
1. Prefix OFF/ON P50/P95 TTFT 및 적중률 비교.
2. KV 설정별 Output throughput 및 P95 TTFT/TPOT 비교.
3. 시간별 KV 사용률/대기 요청 추이 (단위가 다르면 별도 패널).
4. 설정별 preemption 증가량과 시작 로그의 캐시 총용량 표.

HTML은 확인용이며 Word에는 정적 PNG를 사용합니다. 숫자 라벨과 단위를 표시합니다.
스크린샷만 있으면 시계열/요청별 분포는 복원할 수 없습니다.
한 번 측정한 조건 간 차이는 탐색 결과로 표시하고 통계적 유의성/운영 안정성을 주장하지 않습니다.

## 보고서 작성을 위해 보낼 파일

각 실행 ID별 폴더를 통째로 보내면 됩니다.

- benchmark.json, console.log
- metrics.csv, metrics.start.prom, metrics.end.prom
- server.log, server-config.yaml, server-overrides.txt (덮어쓰기가 있으면)
- 생성된 그래프 파일 (있으면)
- vLLM 버전과 nvidia-smi 출력

최소 우선순위: Prefix OFF/ON 두 조건 -> KV base/mem80 두 조건 -> KV seq8 -> len16384 선택.
모든 측정 요청 수는 100입니다. 공식 사전 테스트 요청은 별도로 존재합니다.

## 공식 근거

- https://docs.vllm.ai/en/stable/benchmarking/cli/#prefix-repetition-dataset
- https://docs.vllm.ai/en/stable/cli/bench/serve/
- https://docs.vllm.ai/en/stable/features/automatic_prefix_caching/
- https://docs.vllm.ai/en/stable/usage/metrics/
- https://docs.vllm.ai/en/stable/configuration/optimization/#preemption
- https://docs.vllm.ai/en/stable/cli/serve/#mamba-cache-mode
