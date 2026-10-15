# 새 클라우드 작업에 붙여 넣을 프롬프트

아래 내용을 복사하여, 이 저장소가 연결된 새 클라우드 작업의 첫 메시지로 입력하세요.

---

이 저장소의 vLLM 벤치마킹 과제를 이전 로컬 작업에서 이어서 진행해줘.
먼저 루트 AGENTS.md와 README.md, report-data/base-r3072-o256-c32/README.md를 읽고 현재 상태를 파악해줘.

나는 입문자이고 TTFT/ITL/TPOT 개념은 이해했어. 공식 vLLM CLI 위주로, 파라미터를 바꾸면 무엇이 달라지는지 설명한 뒤 한 번에 하나씩 실험하고 싶어.
최종적으로 실제 결과 수치와 그래프를 포함한 간략한 한국어 Word(.docx) 파라미터 튜닝 보고서를 만들 예정이야.

환경은 Linux GPU 서버, CPU16 cores/RAM32GB/L40S 48GB 1장/Disk500GB/Network10G이고 모델은 Qwen/Qwen3.8-27B-FP8이야.
GPU 서버에서 내가 직접 실행하고 결과를 전달할 거야. 이 클라우드 환경에 GPU나 서버 접속이 있다고 가정하지 말아줘.
서버 로그 파일은 요구하지 않아도 돼. 결과 JSON/콘솔과, 수집했을 경우 metrics.csv로 진행해줘.

현재 상태:
- 기본 조건과 max-num-seqs, max-num-batched-tokens, gpu-memory-utilization, max-model-len, enforce-eager 비교 및 Prefix Caching OFF/ON 측정을 완료했어.
- 최종 요약 보고서는 보고서/vLLM_벤치마킹_보고서.docx, 비교 그래프는 보고서/comparison.png, 측정 요약은 보고서/verified_results.json에 있어.
- 각 실험의 JSON·콘솔·그래프는 벤치마킹 결과/에 있어. 추가 실험은 아직 요청되지 않았고, GPU 서버에 실행 중인 측정도 없어.
- 양자화 실습 결과는 별도 보고서 보고서/Qwen2.5_7B_FP8_양자화_실습정리.docx에 있어. 이는 성능 비교 보고서가 아니라 양자화·서빙·API 사용 과정 요약이야.
- 추가 비교 시 측정 조건이 맞는지 확인하고, KV 사용률이나 Prefix 적중률은 metrics 실측이 없으면 주장하지 말아줘.

공통 부하:
openai-chat, /v1/chat/completions, random 입력3072/출력256, 요청100개, 클라이언트 동시성32,
request-rate inf, seed0, temperature0, ignore-eos, thinking OFF, warmups0, P50/P95.
서버 기본 비교 조건은 memory0.9/max-model-len4096/max-num-batched-tokens2048/Prefix OFF/TP1이야.

B0 결과:
성공100/실패0, 소요207.04초, 출력123.64 token/s.
평균/P95 TTFT: 32.14/46.51초.
평균/P95 TPOT: 109.27/117.85ms.
P50/P95 ITL: 50.77/818.58ms.
평균/P95 E2EL: 60.00/75.53초.
원본 benchmark.json과 console.log, 요청별 CSV 및 PNG 그래프가 report-data/base-r3072-o256-c32/에 있어.
공식 plot 생성은 vllm[bench] 의존성 문제로 실패했지만 JSON으로 그래프를 이미 만들었어.

먼저 기존 보고서와 결과 파일을 읽어 현재 완료 상태를 파악해줘. 이미 측정된 결과를 재실행하거나 완료된 보고서를 중복 생성하지 말아줘. 내가 후속 분석이나 수정을 요청하면 기존 데이터를 사용하고, 데이터가 없는 KV/Prefix 지표를 추정해 사실처럼 표현하지 말아줘.

---
