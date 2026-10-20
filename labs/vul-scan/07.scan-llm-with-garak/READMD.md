# garak 로컬 Qwen 프로브 테스트

## 준비

- 모든 명령은 **프로젝트 루트**에서 실행한다.
- 프로젝트 `.venv`에 garak이 설치되어 있어야 한다. 아래 방법은 garak 0.17.1에서 확인했다.
- 대상은 llama.cpp의 `qwen2.5-7b` 모델이며 API 주소는 `http://127.0.0.1:8080/v1/`이다.
- 서버 구축·시작·종료 방법은 [llama.cpp 서빙 가이드](../../../docs/llama-serving.md)를 참고한다.

서버 상태 확인:

```bash
curl -fsS http://127.0.0.1:8080/health
```

`{"status":"ok"}`가 반환되어야 한다. 연결되지 않으면 서버를 먼저 시작한다.

## 설정과 실행 스크립트

- 설정: [probe-qwen-local.yaml](probe-qwen-local.yaml)
- 스크립트: [run_qwen_probe.py](run_qwen_probe.py)

스크립트는 기존 YAML을 수정하지 않고 사용한다. 현재 설정은 프롬프트당 응답 1개, 순차 처리, 최대 출력 256토큰, 컨텍스트 4096이다.

`--probe-spec`은 **이 스크립트의 옵션**이다. 예전 `probe_spec` 방식 대신 garak 0.17.1 CLI에는 `--spec probes.<모듈>[.<클래스>]`를 전달한다.

## 1. 사용 가능한 프로브 조회·선택

전체 목록만 조회:

```bash
.venv/bin/python labs/vul-scan/07.scan-llm-with-garak/run_qwen_probe.py --list
```

목록에서 번호를 입력하여 실행 (`q`로 종료):

```bash
.venv/bin/python labs/vul-scan/07.scan-llm-with-garak/run_qwen_probe.py
```

encoding 계열 목록만 조회:

```bash
.venv/bin/python labs/vul-scan/07.scan-llm-with-garak/run_qwen_probe.py \
  --list --probe-spec encoding
```

목록은 설치된 garak에서 조회한다. 일부 프로브는 추가 패키지·모델·네트워크 접근이 필요하므로 목록에 있다는 것만으로 실행 성공이 보장되지는 않는다.

## 2. Markdown 이미지 유출 프로브

```bash
.venv/bin/python labs/vul-scan/07.scan-llm-with-garak/run_qwen_probe.py \
  --probe-spec web_injection.MarkdownImageExfil
```

이 프로브는 대화 속 정보를 외부 이미지 URL에 포함한 Markdown을 생성하도록 유도한다. 설치된 버전에서 12개 프롬프트를 사용한다. **Markdown 생성 탐지는 실제 외부 HTTP 요청이나 정보 유출 완료의 증명이 아니다.**

## 3. encoding 단일·전체 테스트

Base64만 테스트:

```bash
.venv/bin/python labs/vul-scan/07.scan-llm-with-garak/run_qwen_probe.py \
  --probe-spec encoding.InjectBase64
```

**encoding 계열 전체 테스트:** 클래스 없이 모듈만 지정한다.

```bash
.venv/bin/python labs/vul-scan/07.scan-llm-with-garak/run_qwen_probe.py \
  --probe-spec encoding
```

설치된 encoding 계열 프로브를 선택한다. Base64, Hex, ROT13 등 여러 인코딩으로 지시를 감싸 모델의 대응을 검사하며, 전체 실행은 단일 프로브보다 오래 걸릴 수 있다. 터미널에 표시되는 프로브 클래스 개수는 프롬프트 개수와 다르다.

실제 요청 없이 프로브 선택과 실행 명령 확인:

```bash
.venv/bin/python labs/vul-scan/07.scan-llm-with-garak/run_qwen_probe.py \
  --probe-spec encoding --dry-run
```

## 4. garak 직접 실행 (스크립트 대신 사용)

```bash
OPENAICOMPATIBLE_API_KEY=local-no-auth \
.venv/bin/python -m garak \
  --config labs/vul-scan/07.scan-llm-with-garak/probe-qwen-local.yaml \
  --spec probes.encoding \
  --report_prefix qwen-encoding-all-01
```

Markdown 테스트는 `--spec probes.web_injection.MarkdownImageExfil`로 변경한다. 재실행 시 `report_prefix`도 변경하여 보고서를 구분한다. 스크립트는 시간과 고유 ID로 접두사를 자동 생성한다.

`local-no-auth`는 인증을 켜지 않은 로컬 서버용 공개 더미 값이다. 실제 OpenAI 키는 필요 없다. 스크립트도 환경 변수가 없으면 이 값을 사용하며, 기존 환경 값은 보존한다. 실제 키를 YAML이나 문서에 저장하지 않는다.

## 5. 결과와 보고서

보고서는 실행 종료 시 garak이 출력하는 정확한 경로에서 확인한다. 현재 YAML의 상대 `report_dir: ./reports`는 프로젝트 루트가 아닌 **garak 데이터 디렉터리 기준**이며, 이 호스트에서는 다음 폴더로 해석된다.

```text
/home/ainsdev/.local/share/garak/reports/
```

- `<report_prefix>.report.jsonl`: 프롬프트·응답·평가 기록
- `<report_prefix>.report.html`: 요약 보고서

JSONL의 `entry_type: eval`에서 `passed`, `fails`, `nones`, `total_evaluated`를 확인한다. `completion` 레코드와 실행 오류도 함께 확인한다. attempt 레코드는 처리 단계별로 중복 기록될 수 있어 단순 줄 수를 테스트 개수로 세지 않는다.

| 결과 | 해석 |
| --- | --- |
| `ok on 8/12` | 12개 중 8개에서 탐지기가 공격 성공 패턴을 찾지 못함 |
| `FAIL` | 일부 응답에서 공격 성공 패턴 탐지. 설치 실패와 다름 |
| `attack success rate` | 해당 탐지기 기준 공격 성공 비율 |
| API 오류·빈 응답·컨텍스트 초과 | 실행 문제로 분리해서 확인. 방어 성공으로 해석하지 않음 |

구축 및 스크립트 검증 시 MarkdownImageExfil을 실제 실행했고, 두 탐지기 각각 12개 평가 중 passed 8 / fails 4 / nones 0이었다. 이는 해당 실행의 기록이며 전반적인 보안성을 보장하지 않는다. encoding 전체 실행은 별도 작업이다.

**안전 주의:** 테스트용 비민감 데이터만 사용한다. 공격 URL이 포함될 수 있으므로 보고서는 우선 텍스트로 확인하고, 출력 Markdown·HTML을 무심코 렌더링하거나 링크를 열지 않는다. `Ctrl+C`로 중단하면 일부 결과만 남을 수 있다.

## Resources

- Introduction to Garak
- [Data Exfiltration: How Sensitive Data Leaks Out](https://embracethered.com/blog/posts/2023/bing-chat-data-exfiltration-poc-and-fix/)
- Hands-on: Profanity Probes (LMRC Probe White Paper, [https://arxiv.org/abs/2303.18190](https://arxiv.org/abs/2303.18190))