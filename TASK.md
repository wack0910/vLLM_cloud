# FP8 양자화 실습 결과 보고서 작성 요청

## 1. 작업 목적

첨부한 실습 자료, Python 코드, 명령어 실행 로그, GPU 모니터링 데이터 및 캡처 이미지를 분석하여 **「LLM FP8 양자화 실습 결과 보고서」**를 작성해줘.

이번 실습은 기존 vLLM 파라미터별 성능 벤치마킹과 별개의 작업이다.

**핵심 목표는 BF16 원본 모델을 FP8로 직접 양자화하고, 그 결과가 실제로 적용되었는지 정량적으로 검증하는 것이다.**

보고서에서는 다음 내용을 중점적으로 다룬다.

1. BF16 원본 모델에서 FP8 양자화를 수행한 방법 및 기술적 원리
2. LLM Compressor의 `oneshot()`과 `QuantizationModifier`를 이용한 양자화 과정
3. 양자화 전후 가중치 정밀도와 모델 저장 용량 변화
4. 양자화 과정에서의 GPU VRAM 사용량 및 소요 시간
5. vLLM에서 양자화 체크포인트를 로드하고 정상적으로 추론하는지 검증
6. 실제 발생한 오류, 해결 과정 및 기술적 분석
7. 양자화 실습을 통해 확인한 결과와 한계

단순 작업 일지가 아니라, **실험 조건, 측정 근거, 실제 결과, 기술적 해석이 포함된 엔지니어링 보고서**로 작성해줘.

---

## 2. 실습 환경

현재 확인된 환경 정보는 다음과 같다.

| 항목 | 환경 |
|---|---|
| GPU | NVIDIA L40S 48GB × 1 |
| GPU 아키텍처 | Ada Lovelace, Compute Capability 8.9 |
| NVIDIA Driver | 595.99.02 |
| NVIDIA-SMI CUDA 표시 | 13.2 |
| PyTorch | 2.13.0+cu130 (기존 vLLM 환경) |
| PyTorch CUDA | 13.0 (기존 vLLM 환경) |
| Python | 3.10.12 |
| 시스템 RAM | 31GiB |
| 디스크 여유 공간 | 약 401GB (사전 점검 시점) |
| 추론 엔진 | vLLM 0.31.0 |
| 양자화 도구 | LLM Compressor |
| 원본 모델 | Qwen/Qwen2.5-7B-Instruct |
| 원본 정밀도 | BF16 |
| 양자화 방식 | FP8_DYNAMIC |
| 결과 저장 형식 | compressed-tensors |

LLM Compressor의 실제 버전과 양자화 전용 가상환경의 PyTorch 버전은 환경 수집 파일에서 확인해 기입해줘.

### 사용한 디렉터리

```text
/root/workspace/
├── vllm-env/
└── quantization/
    ├── quant-env/
    ├── models/
    │   └── Qwen2.5-7B-Instruct/
    ├── outputs/
    │   └── Qwen2.5-7B-FP8-oneshot/
    ├── scripts/
    │   └── quantize_fp8_oneshot.py
    ├── config/
    │   └── fp8-serve.yaml
    ├── logs/
    └── reports/
```

---

## 3. 적용한 FP8 양자화 방식

양자화에는 LLM Compressor의 `oneshot()`과 `QuantizationModifier`를 활용했다.

핵심 양자화 설정은 다음과 같다.

```python
recipe = QuantizationModifier(
    targets="Linear",
    scheme="FP8_DYNAMIC",
    ignore=[
        "lm_head",
        "model.embed_tokens",
    ],
)
```

보고서에서는 다음 사항을 기술적으로 설명해줘.

- Post-Training Quantization(PTQ)의 개념
- BF16과 FP8의 표현 방식 차이
- FP8_DYNAMIC의 가중치 및 활성화 양자화 방식
- `oneshot()`과 `QuantizationModifier`의 역할
- `targets="Linear"`의 의미
- Embedding과 LM Head를 양자화 대상에서 제외한 이유
- Calibration 데이터셋 없이 수행할 수 있는 이유
- FP8 변환 결과가 compressed-tensors 형식으로 저장되는 구조

반드시 실제 사용한 설정을 기준으로 설명하고, FP8_DYNAMIC과 다른 FP8 방식의 특징을 혼동하지 말 것.

---

## 4. vLLM Serving 설정

FP8 양자화 이후 다음과 같은 vLLM 설정으로 모델 로딩 및 추론을 검증하도록 구성했다.

| 파라미터 | 설정값 |
|---|---|
| tensor-parallel-size | 1 |
| gpu-memory-utilization | 0.9 |
| max-model-len | 4096 |
| max-num-seqs | 24 |
| max-num-batched-tokens | 1024 |
| enable-chunked-prefill | true |
| enable-prefix-caching | false |
| kv-cache-dtype | auto |
| enforce-eager | false |
| dtype | auto |

실제 적용 여부는 `fp8-serve.yaml` 및 vLLM 실행 로그로 확인해줘.

특히 양자화 스크립트에 지정하는 설정과 vLLM Serving 시 지정하는 실행 파라미터를 구분해서 설명해야 한다.

`gpu-memory-utilization=0.9`가 모델 가중치만의 메모리 점유율을 의미하지 않는다는 점도 설명해줘.

---

## 5. 보고서 상세 구성

### 5.1 실습 개요

- 양자화 기술을 학습하는 목적
- BF16 모델을 FP8로 변환하는 배경
- FP8 양자화의 일반적인 이점과 제약사항
- 이번 실습에서 확인할 항목과 범위

### 5.2 실습 환경 및 아키텍처

- GPU 및 시스템 자원
- Python, PyTorch, LLM Compressor, vLLM 환경
- 원본 모델 정보
- BF16 원본 → FP8 양자화 → 모델 저장 → vLLM 서빙 구조

전체 처리 흐름은 아키텍처 다이어그램으로 표현해줘.

### 5.3 FP8 양자화 수행 과정

- BF16 원본 모델 확인
- `oneshot()` 양자화 설정
- FP8 변환 실행 과정
- 양자화 완료 로그
- 양자화 과정의 소요 시간 및 자원 사용량
- 결과 모델 저장 방식

가능하면 핵심 코드와 실행 로그를 함께 배치하고, 각 단계가 수행하는 역할을 설명해줘.

### 5.4 양자화 전후 모델 크기 비교

BF16 원본과 FP8 모델의 다음 항목을 비교해줘.

- 모델 전체 디렉터리 저장 크기
- Safetensors 가중치 파일 크기 합계
- 실제 가중치 dtype
- 저장 용량 절감률

계산식:

`절감률(%) = (1 - FP8 가중치 크기 / BF16 가중치 크기) × 100`

모델 크기 비교 결과를 막대그래프로 작성하고 수치를 표기해줘.

측정값이 존재하지 않으면 추정치를 실제 결과처럼 작성하지 말 것.

### 5.5 양자화 중 GPU 및 시스템 자원 분석

다음 항목을 수집한 데이터로 분석해줘.

- 양자화 시작 전 GPU VRAM 점유량
- 양자화 진행 중 GPU VRAM 변화
- 측정된 최대 GPU VRAM
- GPU Utilization 변화
- GPU Power Draw 추이
- 양자화 전체 소요 시간
- CPU 최대 RSS(로그에 존재하는 경우)

`fp8_gpu_usage.csv`를 이용하여 시간에 따른 VRAM 사용량 그래프를 작성해줘.

특히 다음 두 지표를 구분해줘.

1. `nvidia-smi`가 측정하는 GPU 전체 메모리 사용량
2. PyTorch의 `max_memory_allocated()` 또는 `max_memory_reserved()`로 측정한 메모리 사용량

각 수치의 의미와 측정 범위가 다르다는 점을 명시해줘.

### 5.6 FP8 양자화 결과 검증

다음 증거를 분석해줘.

- `config.json`의 `quantization_config`
- Safetensors 가중치 데이터 타입
- 실제 FP8 가중치 존재 여부
- BF16 등으로 유지된 계층
- `embed_tokens.weight_scale` 존재 여부

단순히 디렉터리 이름이 FP8이라고 해서 양자화가 성공했다고 판단하지 말 것.

실제 저장된 가중치와 양자화 설정을 근거로 검증해야 한다.

### 5.7 vLLM 서빙 및 추론 검증

- FP8 체크포인트 로드 여부
- vLLM API 서버 시작 성공 여부
- 모델 가중치 로딩 시간
- 모델 가중치의 GPU 메모리 점유량
- KV Cache 관련 설정 및 로딩 로그
- vLLM 초기화 이후 전체 VRAM 점유량
- OpenAI 호환 API의 정상 응답 여부
- 실제 추론 결과

모델 저장 크기, 모델 가중치 VRAM, KV Cache, 전체 GPU 메모리 사용량을 구분해줘.

기본 추론 검증에는 아래와 같은 질문을 사용했다.

> 127 곱하기 38의 결과만 숫자로 답해줘.

정답은 4826이다.

실제 API 응답이 존재하면 해당 내용을 근거로 검증 결과를 작성해줘.

### 5.8 트러블슈팅

이전 FP8 양자화 결과를 vLLM에 로딩할 때 다음 오류가 발생했다.

```text
ValueError: There is no module or parameter named
'embed_tokens.weight_scale' in Qwen2Model.
```

원인은 체크포인트의 Embedding 스케일 파라미터와 vLLM Embedding 모듈 간 불일치로 분석되었다.

이에 양자화 설정에서 다음 계층을 제외하도록 변경했다.

```python
ignore=[
    "lm_head",
    "model.embed_tokens",
]
```

다음 흐름으로 트러블슈팅 내용을 작성해줘.

- 오류 현상
- 핵심 로그
- 원인 분석
- 설정 수정
- 재양자화
- 수정 후 검증 결과

단, 수정 후 정상 작동 여부는 실제 성공 로그를 근거로 판단하고, 로그가 없다면 해결 완료라고 단정하지 말 것.

### 5.9 종합 분석 및 결론

실제 수집한 데이터를 근거로 다음 내용을 정리해줘.

- FP8 양자화가 정상 수행되었는가?
- BF16 대비 가중치 저장 공간이 얼마나 절감되었는가?
- 양자화에 필요한 GPU 메모리와 시간은 어느 정도였는가?
- vLLM에서 실제 FP8 체크포인트를 정상적으로 서빙할 수 있었는가?
- 양자화 방식의 기술적 장점과 주의점은 무엇인가?
- 향후 GPTQ INT4 양자화 실습에서 추가 검증할 사항은 무엇인가?

---

## 6. 분석에 활용할 파일

아래 파일이 제공되면 실제 내용을 확인하고 반영해줘.

| 파일 | 분석 목적 |
|---|---|
| `01_environment.txt` | 실습 환경 정보 |
| `01_quant_packages.txt` | Python 패키지 버전 |
| `02_fp8_recipe.py` | 실제 양자화 설정 |
| `fp8_oneshot.log` | 양자화 실행 결과 |
| `fp8_gpu_usage.csv` | 양자화 중 GPU 사용량 추이 |
| `03_fp8_gpu_peak.txt` | 측정된 최대 VRAM |
| `03_fp8_resource_summary.txt` | 작업 소요 시간 및 메모리 |
| `04_size_comparison.txt` | 모델 크기와 절감률 |
| `05_fp8_config.txt` | 양자화 메타데이터 |
| `05_fp8_dtype.txt` | 실제 가중치 dtype |
| `fp8-serve.yaml` | vLLM Serving 설정 |
| `fp8_vllm.log` | 모델 로딩 및 서버 기동 로그 |
| `07_fp8_serving_gpu.txt` | vLLM 구동 시 GPU 상태 |
| `08_fp8_models.json` | 서빙 모델 정보 |
| `08_fp8_inference.json` | 모델 추론 응답 |

실제 디렉터리에 존재하지 않거나 제공되지 않은 파일은 존재한다고 가정하지 말고, 추가 수집이 필요한 자료로 정리해줘.

기존 `vLLM_벤치마킹_결과_보고서.docx`는 **보고서의 문서 스타일과 구성 참고용**이다. 해당 문서의 27B 모델 벤치마킹 수치를 이번 7B FP8 양자화 실험 결과로 혼용하지 말 것.

---

## 7. 보고서 시각화 요구사항

다음 그래프와 표를 우선 작성해줘.

**그래프**

1. BF16 vs FP8 가중치 저장 크기 비교
2. FP8 양자화 과정의 시간별 VRAM 사용량
3. GPU Utilization 시간별 변화(데이터가 존재하는 경우)

**표**

1. 실습 환경 구성
2. FP8 양자화 파라미터
3. BF16·FP8 모델 저장 크기 및 절감률
4. 양자화 시간과 GPU 메모리 분석
5. FP8 체크포인트 검증 결과
6. vLLM 로딩 및 추론 검증 결과
7. 트러블슈팅 요약

그래프에는 축 이름과 단위를 정확히 표시하고, 표의 모든 실제 수치는 원본 로그에서 확인할 수 있어야 한다.

---

## 8. 보고서 작성 조건

- 문체는 기술 엔지니어링 보고서 형식으로 작성한다.
- 마케팅성 표현이나 검증되지 않은 성능 우수성 주장은 사용하지 않는다.
- 명령어와 실행 로그는 핵심적인 부분만 발췌하고 의미를 설명한다.
- 캡처 이미지는 실험 결과를 증빙하는 위치에 배치한다.
- 각 캡처와 그래프에는 번호 및 설명을 추가한다.
- 기술적 설명은 vLLM 및 LLM Compressor 공식 문서를 우선 근거로 사용한다.
- 직접 측정한 결과와 이론적 예상값을 명확하게 구분한다.
- 측정되지 않은 값은 `미측정`, 자료가 없는 경우 `자료 미제공`, 검증되지 않은 항목은 `검증 필요`로 표기한다.
- 향후 INT4 양자화 결과를 추가하여 비교 보고서로 확장할 수 있는 구조로 작성한다.

## 9. 최종 산출물

1. **LLM FP8 양자화 실습 결과 보고서.docx** — 최종 편집 가능한 문서
2. **LLM FP8 양자화 실습 결과 보고서.pdf** — 공유 및 열람용
3. 보고서에 삽입한 그래프 원본
4. 미확보 데이터 및 추가 측정 필요 항목 정리

보고서 분량은 실제 확보된 자료에 맞춰 약 7~10페이지를 목표로 한다.

기존 vLLM 파라미터 벤치마킹 보고서 수준으로 기술적 근거와 수치 분석을 갖추되, 이번 실습의 핵심인 **양자화 작업 자체의 재현성, 가중치 변환 검증, 저장 공간 절감, GPU 자원 요구량**을 명확히 보여주는 방향으로 작성해줘.