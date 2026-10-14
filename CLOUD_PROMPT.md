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
- 완료: B0 서버 max-num-seqs16, 나머지 서버 설정은 config/config-base.yaml.
- 진행 중: max-num-seqs만32로 바꾸고 vllm serve --config config/config.yaml로 재시작한 뒤 동일 부하 실행.
- seq32 결과는 아직 전달하지 않았어. Prefix/KV 추가 튜닝 실험은 아직 시작하지 않았어.
- 현재 CLI 전체는 bench/seq32.sh에 있어. 새 실행을 중복으로 시키거나 부하를 변경하지 말아줘.

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

우선 위 상태를 짧게 확인하고 seq32 결과를 받을 준비를 해줘. 아직 결과가 없으면 완료·개선율을 만들어내지 말아줘.
결과를 전달하면 먼저 부하 조건 일치를 확인한 뒤 B0와 seq32를 수치·변화율·비교 그래프로 분석해줘.
데이터가 없는 KV 부족이나 Prefix 효과를 단정하지 말고, 이후 실험은 결과를 설명한 다음 하나씩 제안해줘.
최종 보고서는 환경/실험 조건, 비교표와 그래프, 관찰 결과, 권장 설정과 수치 근거 중심으로 간략하게 작성해줘.

---
