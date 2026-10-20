# llmfit 모델 선정부터 llama.cpp Qwen 설치·검증까지

이 문서는 현재 호스트에서 수행한 **하드웨어 확인 → llmfit 추정 → Qwen 선정 → llama.cpp CUDA 빌드 → GGUF 다운로드 → API 검증 → garak 연동** 과정을 정리한다. 설치를 반복할 필요는 없으며, 기존 설치에서는 확인 명령만 실행하면 된다.

명령은 Linux 호스트에서 실행한다. `.venv/bin/python`과 `labs/...` 경로를 사용하는 명령은 프로젝트 루트에서 실행한다. `~/tools`와 `~/models`는 저장소 밖의 사용자 홈 경로다.

## 대상과 환경

- 모델: `Qwen/Qwen2.5-7B-Instruct-GGUF`, Q8_0 (공식 Qwen GGUF 저장소).
- 용도: 일반 Instruct 모델에 대한 encoding, prompt injection 등 garak 보안 실습.
- 호스트: NVIDIA RTX 4070 Ti 12GB, RAM 약 30.53GB.
- llmfit: 컨텍스트 4096에서 Good, 예상 메모리 8.72GB, 예상 생성 속도 36.4 tok/s. 이는 추정이며 실제 벤치마크가 아니다.
- `EmergentMethods/Phi-3-mini-4k-instruct-graph`는 별개의 그래프 추출 특화 모델이다. 이 문서의 서버는 그 모델을 사용하지 않는다.
- API: `http://127.0.0.1:8080/v1`, 모델 별칭 `qwen2.5-7b`.
- garak은 저장소 `.venv`의 0.17.1 기준이다.

## 0. llmfit 실행과 모델 선정

### 도구와 하드웨어 확인

```bash
command -v llmfit
llmfit --version
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv
llmfit --json system
command -v git cmake nvcc uvx
nvcc --version
```

이 호스트에는 `llmfit 1.1.17`이 설치되어 있다. llmfit이 없는 새 호스트는 먼저 공식 배포 안내에 따라 설치해야 한다. llmfit은 모델 적합성을 추정하는 도구이며 이 절의 명령은 llama.cpp나 가중치를 설치하지 않는다.

### 후보 추천과 정확한 모델 조회

```bash
llmfit --max-context 4096 recommend \
  --use-case chat --runtime llamacpp -n 5

llmfit --max-context 4096 info Qwen/Qwen2.5-7B-Instruct --json
```

| 조회 항목 | 이 호스트에서 확인한 값 |
| --- | --- |
| GPU | NVIDIA GeForce RTX 4070 Ti, 12GB급 |
| 시스템 RAM | 약 30.53GB |
| 모델 | `Qwen/Qwen2.5-7B-Instruct` |
| 추정 컨텍스트 | 4096토큰 |
| `fit_level` | Good |
| `best_quant` | Q8_0 |
| `memory_required_gb` | 8.72GB |
| `estimated_tps` | 36.4 tok/s |

**이 수치는 llmfit 추정값이며 실제 처리량 측정값이 아니다.** 추천 목록은 카탈로그·버전·필터에 따라 바뀔 수 있다. 임베딩 모델이나 특정 작업 특화 모델을 단순 순위만으로 garak의 일반 대화 대상 모델로 선택하지 않는다.

일반적인 encoding·prompt injection 비교 실습에는 일반 Instruct 모델인 Qwen을 선택했다. Q8_0은 이 호스트에 적합하다고 추정되었고 낮은 비트 양자화보다 양자화 영향을 줄일 수 있어 사용했다. 메모리 여유를 우선하면 Q4_K_M을 별도로 검토하되, 그 결과를 Q8_0 실행 결과와 혼동하지 않는다.

`EmergentMethods/Phi-3-mini-4k-instruct-graph`는 그래프 추출 특화 모델이므로 일반 Qwen 기준 테스트와 목적이 다르다. 해당 서비스를 평가하려면 그 모델과 운영 프롬프트를 그대로 사용해야 한다.

현재 서버가 이미 가중치를 올린 상태라면 GPU 여유 메모리가 설치 전보다 작게 나온다. llmfit의 총 VRAM 기반 적합도만 보고 같은 GPU에 서버를 하나 더 실행하면 OOM이 발생할 수 있다. llmfit의 `installed: false` 역시 수동 다운로드한 GGUF 파일이 없다는 증명은 아니다.

## 1. CUDA 빌드

필요 도구: git, CMake, C++ 컴파일러, CUDA Toolkit(nvcc). NVIDIA 드라이버의 CUDA 표시는 Toolkit 설치 여부와 다르다.

```bash
mkdir -p "$HOME/tools"
git clone --depth 1 https://github.com/ggml-org/llama.cpp.git "$HOME/tools/llama.cpp"
cmake -S "$HOME/tools/llama.cpp" -B "$HOME/tools/llama.cpp/build" \
  -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=ON
cmake --build "$HOME/tools/llama.cpp/build" --config Release -j 8 --target llama-server
"$HOME/tools/llama.cpp/build/bin/llama-server" --list-devices
```

이미 소스가 있으면 clone을 반복하지 않는다. GPU 장치가 표시되는지 확인한다. 재현 시 `git -C ~/tools/llama.cpp rev-parse HEAD`로 빌드 커밋을 기록한다.

## 2. Q8_0 가중치 다운로드

```bash
uvx --from huggingface-hub hf download Qwen/Qwen2.5-7B-Instruct-GGUF \
  --include 'qwen2.5-7b-instruct-q8_0-*.gguf' \
  --local-dir "$HOME/models/qwen2.5-7b"
```

세 조각을 모두 같은 폴더에 둔다. llama-server에는 첫 번째 조각을 전달한다. 파일 크기와 실행 VRAM 사용량은 다르다.

다운로드 파일 확인:

```bash
find "$HOME/models/qwen2.5-7b" -maxdepth 1 -name 'qwen2.5-7b-instruct-q8_0-*.gguf' -printf '%f %s bytes\n'
```

완료된 파일명이 `00001-of-00003`, `00002-of-00003`, `00003-of-00003`인 GGUF 세 개가 있어야 한다. 중간 다운로드 파일만 있는 상태로 서버를 시작하지 않는다. 이 모델은 공개 GGUF를 직접 내려받으므로 별도의 Safetensors 변환·양자화 작업이 필요 없다.

## 3. 서버 시작 및 종료

8080 포트가 비어 있는지 확인하고, 사용하지 않는 Jupyter GPU 커널을 먼저 종료한다. 다른 작업의 프로세스를 임의로 종료하지 않는다.

```bash
ss -ltn '( sport = :8080 )'
nvidia-smi
"$HOME/tools/llama.cpp/build/bin/llama-server" \
  --model "$HOME/models/qwen2.5-7b/qwen2.5-7b-instruct-q8_0-00001-of-00003.gguf" \
  --alias qwen2.5-7b --n-gpu-layers 99 --ctx-size 4096 --parallel 1 \
  --host 127.0.0.1 --port 8080
```

현재 터미널에서 실행하면 Ctrl+C로 종료한다. `127.0.0.1` 바인딩은 로컬 접근만 허용한다. Remote SSH 사용자는 원격 터미널에서 호출하거나 SSH 포트 포워딩을 사용한다. 인증 없이 공인 네트워크에 노출하지 않는다.

## 4. API 검증

다른 터미널에서 실행한다.

```bash
curl -fsS http://127.0.0.1:8080/health
curl -fsS http://127.0.0.1:8080/v1/models
curl -fsS http://127.0.0.1:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"qwen2.5-7b","messages":[{"role":"user","content":"Say hello in one short sentence."}],"temperature":0,"max_tokens":64,"stream":false}'
```

health 성공뿐 아니라 choices[0].message.content가 비어 있지 않은지 확인한다. 서버 로그에서 GPU 오프로딩을 확인한다. API smoke test는 속도 벤치마크가 아니다.

## 5. garak 설정

설정 파일: `labs/vul-scan/07.scan-llm-with-garak/probe-qwen-local.yaml`.

```yaml
run:
  generations: 1
system:
  parallel_requests: 1
  parallel_attempts: 1
plugins:
  target_type: openai.OpenAICompatible
  target_name: qwen2.5-7b
  generators:
    openai:
      OpenAICompatible:
        uri: http://127.0.0.1:8080/v1/
        temperature: 0.0
        max_tokens: 256
        context_len: 4096
        stop: []
reporting:
  report_dir: ./reports
```

`openai.OpenAICompatible`은 로컬 API를 호출하며 OpenAI 클라우드 모델을 뜻하지 않는다. stop을 비워 기본 `#`, `;` 중단 문자열의 영향을 없앤다. 모델 별칭과 서버 포트를 변경하면 YAML 및 API 검증 명령도 함께 변경한다.

프로젝트 루트에서 실행:

```bash
export OPENAICOMPATIBLE_API_KEY=local-no-auth
.venv/bin/python -m garak \
  --config labs/vul-scan/07.scan-llm-with-garak/probe-qwen-local.yaml \
  --spec probes.web_injection.MarkdownImageExfil \
  --report_prefix qwen-markdown
```

`local-no-auth`는 SDK의 비어 있지 않은 키 요구를 만족하는 공개 더미 값이다. 위 서버는 인증을 켜지 않았으므로 실제 키는 필요 없다.

Encoding 프로브 전체:

```bash
.venv/bin/python -m garak \
  --config labs/vul-scan/07.scan-llm-with-garak/probe-qwen-local.yaml \
  --spec probes.encoding --report_prefix qwen-encoding
```

전체 encoding 스캔은 요청 수가 많을 수 있다. 빠른 초기 검증에는 아래를 사용할 수 있다.

```bash
.venv/bin/python -m garak \
  --config labs/vul-scan/07.scan-llm-with-garak/probe-qwen-local.yaml \
  --spec probes.encoding.InjectBase64 --report_prefix qwen-base64
```

## 주의와 해석

- 테스트용 비민감 데이터만 사용한다. 보고서의 공격 URL은 브라우저에서 렌더링하지 않는다.
- Markdown 생성 탐지는 실제 네트워크 유출 증명이 아니다.
- 컨텍스트 초과, API 오류, 빈 응답은 안전 방어 성공으로 보지 않는다.
- 입력과 출력 합계가 4096 이내여야 한다. 긴 프로브는 실행 오류 여부를 확인한다.
- 양자화/프롬프트 템플릿/생성 설정에 따라 결과가 달라진다. 배포 모델과 다른 결과를 일반화하지 않는다.
- 실제 서비스 보안 평가는 운영 시스템 프롬프트, RAG, 도구 권한을 포함한 서비스 엔드포인트를 대상으로 별도 진행한다.

## 검증 기록

아래는 구축 당시 실제 실행 기록이다. PID·GPU 사용량은 현재 상태를 보장하지 않으므로 다시 확인한다. 문서 보강 시 llmfit 1.1.17로 정확한 Qwen 모델을 재조회했고 위의 Good/Q8_0/8.72GB/36.4 tok/s 추정값을 확인했다.

- llama.cpp 빌드 커밋: `3bb63cbcbfb62056c84fe9e521b0f3d756d29c32`. CUDA Toolkit 12.0으로 Release 빌드 성공.
- `--list-devices`: NVIDIA GeForce RTX 4070 Ti 인식.
- 공식 Q8_0 GGUF 세 조각 다운로드 완료. `/v1/models`에서 Q8_0 및 모델 별칭 확인.
- `/health`: `{"status":"ok"}`. 채팅 smoke 요청 응답: `Hello!`.
- 서버 PID(구축 시점): `205592`. GPU 점유: `7758 MiB`. 현재 세션 종료 후에도 실행되도록 시작했으나, 시스템 부팅 시 자동 실행하는 서비스는 설치하지 않았다.
- garak `web_injection.MarkdownImageExfil`: 12개 모두 평가, 두 detector 각각 passed 8 / fails 4 / nones 0, 공격 성공률 33.33%, 프로세스 exit code 0.
- 위 FAIL은 설치 실패가 아니라 모델 응답에서 탐지기가 공격 성공 패턴을 발견했다는 뜻이다. 실제 외부 HTTP 유출을 검증한 것은 아니다.
- JSONL: `/home/ainsdev/.local/share/garak/reports/qwen-markdown-setup.report.jsonl`.
- HTML: `/home/ainsdev/.local/share/garak/reports/qwen-markdown-setup.report.html`. 공격 URL이 포함될 수 있어 우선 JSONL을 텍스트로 확인한다.
- garak의 상대 `report_dir`는 현재 작업 폴더가 아니라 garak 데이터 디렉터리 기준이다. 위 YAML의 `./reports`는 `/home/ainsdev/.local/share/garak/reports`로 해석된다.
- 전체 encoding 프로브는 실행하지 않았다. 이 검증은 부하/성능 벤치마크 또는 전반적 안전성 보증이 아니다.

현재 서버 종료(먼저 PID와 명령이 일치하는지 확인):

```bash
ps -p 205592 -o pid,args
kill -TERM 205592
```

재시작은 위의 서버 시작 명령을 사용한다. PID는 재시작하면 달라진다.

## 문제 해결과 완료 기준

| 증상 | 확인·대응 |
| --- | --- |
| `nvcc` 없음 / CUDA 빌드 실패 | Toolkit 설치·컴파일러 호환성과 CMake 오류 로그 확인. 드라이버 설치만으로 Toolkit이 제공되지는 않음 |
| 8080 사용 중 | 기존 서버의 `/health`, `/v1/models`부터 확인. 같은 서버를 중복 실행하지 않음 |
| GPU OOM | `nvidia-smi`로 점유 확인. 노트북 탭만 닫아서는 커널이 남을 수 있으므로 본인 작업의 커널을 명시적으로 종료 |
| GGUF 조각 누락 | 세 조각 다운로드가 모두 끝났는지 확인하고 동일 다운로드 명령 재실행 |
| API 모델 이름 오류 | 서버 `--alias`와 요청의 `model`, garak YAML의 `target_name` 일치 확인 |
| garak 컨텍스트 초과 | 입력과 출력 길이 및 서버 컨텍스트 확인. 실행 오류를 방어 성공으로 해석하지 않음 |

완료 확인 항목:

- [ ] llmfit으로 정확한 모델 ID와 컨텍스트를 조회했다.
- [ ] CUDA 빌드가 성공하고 `--list-devices`에 GPU가 표시된다.
- [ ] GGUF 세 조각을 모두 다운로드했다.
- [ ] `/health`가 정상이며 `/v1/models`의 별칭과 Q8_0을 확인했다.
- [ ] 채팅 API에서 비어 있지 않은 실제 응답을 받았다.
- [ ] garak 프로브가 완료되고 JSONL 평가 기록을 확인했다.

프로브별 실행·전체 encoding 선택 방법은 [garak 실습 문서](../labs/vul-scan/07.scan-llm-with-garak/READMD.md)를 참고한다.
