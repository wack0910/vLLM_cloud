# Qwen3.8-27B-FP8 / L40S 단일 GPU 벤치마크

**도구 출처:** 공식 벤치마크는 `vllm bench serve`입니다. `run_bench.py`는 이 대화에서
Codex가 작성한 YAML 실행 보조 파일이며 공식 vLLM 제공 스크립트가 아닙니다.
YAML 파일도 이번 실험용으로 작성한 것이며 공식 배포 템플릿은 아닙니다.
학습과 재현을 위해 공식 CLI를 직접 사용해도 동일한 측정을 수행할 수 있습니다.

`config.yaml`은 서버 설정, `bench.yaml`은 부하 생성 클라이언트 설정입니다.
둘 다 **공식 기본값 전체 목록이 아니라, 기본값을 일부 유지하고 해당 환경에 맞춰 수정한 시작 설정**입니다.
주석의 `[기본 유지]`와 `[실험 설정]`을 확인하세요. 생략한 옵션은 설치한 vLLM 버전의 기본값입니다.

## 환경과 모델 적합성

- 대상: Linux, 16 CPU cores, 시스템 RAM 32GB, NVIDIA L40S 48GB 1장.
- 모델: `Qwen/Qwen3.8-27B-FP8`. 공식 모델 카드와 vLLM recipe에서 지원을 확인했습니다.
- FP8이므로 BF16 27B보다 가중치 메모리가 작습니다. 단순 27B × 1 byte는 약 27GB이지만,
  비양자화 가중치, scale, activation, KV cache, recurrent state, CUDA graph 메모리가 추가됩니다.
  **L40S에서 4096 문맥·작은 동시성으로 시작 가능한 것으로 판단한 설정이며, 실제 기동은 검증하지 못했습니다.**
- 이 모델은 vision encoder와 hybrid attention을 포함합니다. 텍스트 실험에서는
  `language-model-only: true`로 멀티모달 입력을 사용하지 않습니다.
- 원본 문맥은 262,144 토큰입니다. 처음에는 `max-model-len: 4096`을 사용합니다.
- thinking은 기본 활성화됩니다. 이 실험에서는 서버 기본값과 벤치마크 요청 모두에서 끕니다.
- FP8 가중치 양자화는 모델 config에서 감지합니다. `dtype: auto`가 가중치를 BF16으로
  다시 양자화한다는 뜻은 아닙니다. KV cache의 dtype도 별도 설정입니다.
- 호환되는 최근 안정 vLLM/Transformers 조합을 사용하고 실제 버전을 기록하세요.
  공식 recipe는 Transformers >= 5.8.0을 안내하지만 recipe의 다른 GPU 설정을 L40S에 그대로 적용하지 마세요.
- 32GB 시스템 RAM은 모델 로딩·토크나이저 준비 과정에서 여유가 크지 않을 수 있습니다.
  시스템 OOM인지 GPU OOM인지 로그로 구분하세요. 두 엔진은 순서대로 실행합니다.

## 실행 (Linux Bash, 이 디렉터리에서)

터미널 A, 서버:

```bash
vllm --version
vllm serve --config config.yaml
```

서버 준비가 끝나면 터미널 B에서 먼저 소규모 기동 확인:

```bash
python run_bench.py --config bench.yaml --num-prompts 10 --num-warmups 2 --max-concurrency 1 --label smoke
```

정상 응답을 확인한 후 본 측정:

```bash
python run_bench.py --config bench.yaml
```

실행할 공식 명령만 확인:

```bash
python run_bench.py --config bench.yaml --dry-run
```

### 벤치마크 YAML 실행 보조 파일을 제공하는 이유

확인한 vLLM CLI 소스의 config 처리기는 `vllm bench serve --config bench.yaml`에서
YAML 옵션을 `bench`와 `serve` 사이에 삽입합니다. 따라서 이 중첩 CLI 형태에서
직접 `--config`가 동작한다고 가정하지 않습니다. 또한 현재 `vllm.benchmarks.serve`
모듈에는 독립 실행용 `__main__`이 없어 `python -m ...`으로 우회하지 않았습니다.

`run_bench.py`는 PyYAML로 설정을 읽고 `vllm bench serve --옵션 값 ...`을 실행합니다.
측정 자체는 전부 **공식 vLLM 도구**가 수행하며, 별도의 측정 도구를 설치하지 않습니다.
PyYAML은 vLLM 환경의 의존성을 사용합니다. 설치 버전에 따라 실제 동작은 달라질 수 있습니다.
명령행으로 추가한 일반 스칼라 옵션은 YAML 값을 덮어씁니다.

## 먼저 변경할 값

| 파일 | 옵션 | 시작값 | 비교 후보 |
|---|---|---:|---|
| config.yaml | max-num-seqs | 16 | 8, 16, 32 |
| config.yaml | max-num-batched-tokens | 2048 | 1024, 2048, 4096 |
| bench.yaml | max-concurrency | 4 | 1, 4, 8, 16, 32 |
| bench.yaml | random-input-len | 1024 | 128, 1024, 2048 |
| bench.yaml | random-output-len | 128 | 128, 256 |

서버 YAML을 수정한 뒤에는 서버를 종료하고 재시작해야 합니다. 실행 중에 자동 반영되지 않습니다.
벤치마크 YAML은 다음 측정 실행에 반영됩니다.
`max-num-seqs`는 서버 처리 한도이고 `max-concurrency`는 클라이언트 동시 요청 한도입니다.

1. 서버 설정을 고정하고 동시 요청 수를 비교합니다.
2. 서버 설정을 비교할 때는 동시 요청 수를 32로 고정하고 `max-num-seqs`를 8/16/32로 바꿉니다.
   동시 요청이 4개뿐이면 서버 한도 16과 32의 차이가 드러나기 어렵습니다.
3. 시퀀스 수를 고정하고 `max-num-batched-tokens`를 비교합니다.
4. 각 조건을 3회 반복하고 요청 실패, 평균/p95 TTFT·TPOT, 출력 tok/s를 비교합니다.
   이는 해당 워크로드의 단기 성능 비교이며 장시간 운영 안정성 검증은 아닙니다.

수정 없이 한 조건을 잠깐 바꾸는 예:

```bash
vllm serve --config config.yaml --max-num-seqs 32
python run_bench.py --config bench.yaml --max-concurrency 32 --label seq32-batch2048-c32
```

생성 결과는 `results/vllm` 아래 JSON으로 저장됩니다. 각 실험에서 서버 YAML 사본과
`vllm --version`, GPU/드라이버 정보도 별도로 기록하세요.
무작위 데이터는 처리 성능 측정용이며 답변 품질 평가에는 사용하지 않습니다.
`ignore-eos: true`는 조기 종료를 억제하는 성능 실험 설정입니다.
실제 입력 길이는 템플릿/토큰 재인코딩으로 달라질 수 있으므로 결과의 토큰 수를 확인하세요.

## 메모리 부족 시

- 서버 시작 또는 CUDA graph capture에서 GPU OOM: 먼저 `max-num-seqs: 8`로 줄여 재시작합니다.
  계속 실패하면 `enforce-eager: true`로 기동 가능 여부를 확인합니다.
- prefill 중 GPU OOM: `max-num-batched-tokens: 1024`로 낮춰 재시도합니다.
- CUDA graph/activation에 여유가 필요한 경우 `gpu-memory-utilization: 0.85`도 비교할 수 있습니다.
  이 값은 가중치 자체를 줄이지 않으며 낮추면 캐시에 쓸 공간도 줄어듭니다.
- 입력+출력 길이 또는 캐시 용량 오류: 문맥 길이·동시성을 줄이고 시작 로그의 캐시 용량을 확인합니다.
- 기동 경로/정밀도 변경은 성능에 영향을 줍니다. 바꾼 설정은 모든 비교 조건에 동일하게 적용합니다.
- 모델 아키텍처 미지원, processor 또는 FP8 커널 오류는 메모리 문제와 다릅니다.
  먼저 설치 버전과 공식 모델 recipe를 확인하세요.

## 참고 자료와 검증 범위

확인일: 2026-10-14 (Asia/Seoul).

- [공식 모델 카드](https://huggingface.co/Qwen/Qwen3.8-27B-FP8)
- [공식 vLLM Qwen3.8 recipe](https://recipes.vllm.ai/Qwen/Qwen3.8-27B)
- [서버 CLI](https://docs.vllm.ai/en/stable/cli/serve/)
- [벤치마크 CLI](https://docs.vllm.ai/en/stable/cli/bench/serve/)
- [설정 파서 소스](https://github.com/vllm-project/vllm/blob/main/vllm/utils/argparse_utils.py)
- [CLI 진입점](https://github.com/vllm-project/vllm/blob/main/vllm/entrypoints/cli/main.py)

로컬 Windows 작업 공간에는 vLLM과 원격 L40S 접속 환경이 없습니다.
따라서 GPU 모델 로딩이나 실제 벤치마크는 수행하지 않았습니다.
모든 옵션은 조사한 공식 문서/소스에 맞춰 작성했으며 실행 보조 파일의 옵션 변환은 별도로 확인했습니다.
PyYAML 문법 검사, 모델/URL/길이 일치 검사, 중첩 JSON·불리언 옵션 변환,
명령행 덮어쓰기, dry-run 및 공식 CLI 호출 경로 검사를 통과했습니다.
