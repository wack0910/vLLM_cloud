# B0: 기준 설정 측정 기록

- 모델: Qwen/Qwen3.8-27B-FP8 / 사용자 환경 L40S 1장.
- 실행 ID: base-r3072-o256-c32.
- 공식 vllm bench serve, openai-chat, /v1/chat/completions.
- random 입력 목표3072/출력256, 측정100개, 동시성32, request-rate inf.
- seed0, temperature0, ignore-eos, thinking OFF, 별도 워밍업0.
- 공식 사전 단일 요청 테스트는 별도 수행됨.
- 서버 설정은 사용자가 공유한 config 기준이며 실제 시작 로그는 미제공.
- 공유 서버 설정: memory0.9, model-len4096, seq16, batched-tokens2048, Prefix OFF.
- vLLM 버전/실제 캐시 용량/모니터링 CSV는 미제공.

## 결과

| 지표 | 평균 | P50 | P95 |
|---|---:|---:|---:|
| TTFT (s) | 32.140 | 34.785 | 46.514 |
| TPOT (ms) | 109.268 | 113.816 | 117.846 |
| ITL (ms) | 108.841 | 50.773 | 818.578 |
| E2EL (s) | 60.003 | 63.809 | 75.534 |

- 성공100/실패0, 소요207.0449초, 요청 처리량0.48299 req/s.
- 출력 처리량123.64468 token/s, 총 처리량1613.36027 token/s.
- 입력308438토큰 (요청별 평균3084.38, 최소3083, 최대3086).
- 출력25600토큰, 모든 요청256토큰.
- 저장된 ITL 관측25600개 중500ms 초과2011개 (7.8555%). 요청 실패 비율이 아님.
- JSON 배열로 평균TPOT 및 각 지표의P50/P95를 재계산하여 공식 요약과 일치 확인.

## 해석 범위

일반 채팅에서는 첫 응답 대기와 일부 스트리밍 간격이 긴 조건이다.
입력 처리와 동시 요청 대기가 영향을 줄 수 있지만, KV 부족/preemption이 원인인지는
현재 자료만으로 확정하지 않는다. Prefix는 OFF이며 재사용 효과를 측정한 실행이 아니다.
실패0은 이번 단기 실행의 결과이며 장시간 운영 안정성 증명은 아니다.
Peak concurrency34는 실제 동시 제한 위반으로 단정하지 않는다. 계산 방식은 설치 버전 확인이 필요하다.

## 그래프와 원본

- baseline-summary.png: 보고서용 요약 그래프, JSON에서 생성.
- request-timeline.png: 전송 시작/첫 토큰/완료 기록에서 재구성한 타임라인.
- 이 두 PNG는 공식 vLLM 그래프 출력이 아니라 본 과제용 재구성 그래프다.
- 타임라인의 주황색은 TTFT 전체이며 순수 prefill 시간이나 GPU 실행시간이 아니다.
- 타임라인에는 클라이언트에서 전송 전에 대기한 시간은 표시하지 않는다.
- requests.csv: 요청별 수치, 단위는 헤더에 명시.
- analysis.json: 요약 및 파생 통계.
- benchmark.json / console.log: 첨부 원본 보존.
- server-config-reported.yaml: 사용자 공유 설정에 해당하는 작업 폴더 사본. 서버 적용 검증은 아님.
- 보고서용 PNG 생성으로 그래프 재생성을 위한 GPU 벤치마크 재실행은 불필요하다.
- KV 사용률/Prefix 적중률 시계열은 기존 JSON에서 복원할 수 없다.

## 다음 비교 조건

서버 max-num-seqs만16 ->32로 변경하고 다른 서버 설정과 벤치 부하를 유지한다.
결과 폴더/label만seq32-r3072-o256-c32로 변경한다. 서버를 재시작하고 /metrics를 수집한다.
설정별 실제 캐시 용량, 요청 대기 및 preemption과 함께 판단한다.
아직 추천 최종 설정을 선정한 상태가 아니다.

## 참고

- https://docs.vllm.ai/en/stable/configuration/optimization/#chunked-prefill
- https://docs.vllm.ai/en/stable/usage/metrics/#general-metrics
