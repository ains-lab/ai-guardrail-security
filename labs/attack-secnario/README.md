# AI Guardrail 핸즈온 랩 (패스트캠퍼스 11월 강의용)

사내 업무 비서(RAG + 도구 호출)를 **일부러 취약하게** 만들고, 공격 시나리오를 자동 실행·채점하는 실습 환경.
외부 패키지 없이 Python 표준 라이브러리만 쓴다 (3.9+).

```
fcg/data.py           가짜 문서·직원·DB, 유출 탐지용 CANARY 문자열
fcg/tools.py          도구 5개 (search_docs, get_employee, send_email, run_sql, issue_refund) — 취약점 W1~W4, W11 내장
fcg/agent.py          에이전트 루프 + Rail 훅 4곳 (input / retrieval / tool_call / output)
fcg/rails.py          Rail 인터페이스            ← Step 4 가 구현하는 지점
fcg/example_rails.py  Rail 예시 (데모용, Step 4 산출물 아님)
fcg/llm.py            mock LLM / OpenAI 호환 어댑터
fcg/judge.py          결정론적 채점 (EXPLOITED / EXPOSED / BLOCKED, PASS / FAIL)
owasp/scenarios.json     OWASP LLM Top 10 계열: 공격 16(A01~A15, A22) + 정상 업무 6
asi/scenarios.json       에이전트(ASI) 계열: 공격 7(A16~A21, A23) + 정상 업무 2  (둘을 합쳐 31건)
run_scenarios.py      실행기 · 리포트 · before/after 비교 · RAGAS 입력 내보내기
../eval/eval_ragas.py Step 3 RAGAS 평가 (Faithfulness, Context Relevance). ../eval/requirements-ragas.txt 필요, Python 3.11/3.12
tests/test_smoke.py   하네스 배선 테스트
docs/                 시나리오 설계서, Step 2 / Step 4 인수인계, 현황, Udemy 대응표
```

## 실행

```powershell
# 프로젝트 루트에서
python run_scenarios.py --label baseline                                  # 방어 없음, owasp + asi 전체 31건
python run_scenarios.py --suite owasp --label owasp-only                  # owasp/scenarios.json 만 (22건)
python run_scenarios.py --suite asi --label asi-only                      # asi/scenarios.json 만 (9건)
python run_scenarios.py --label partial --rails fcg.example_rails:build   # 예시 레일 (일부러 불완전)
python run_scenarios.py --label full    --rails fcg.example_rails:build_full
python run_scenarios.py --compare results/baseline_results.json results/full_results.json   # Step 5 비교표
python -m unittest discover -s tests -v

# 실제 LLM (OpenAI 호환: OpenAI / Ollama / vLLM ...)
$env:FCG_API_KEY = "sk-..."                       # Ollama 면 아무 값
$env:FCG_BASE_URL = "https://api.openai.com/v1"   # 생략 시 OpenAI
python run_scenarios.py --llm openai --model gpt-4o-mini --label baseline-gpt
```

산출물: `results/<label>_results.json`(전체 트레이스), `_report.md`, `_ragas.jsonl`(Step 3 입력).

## 꼭 알아둘 것

- **기본값 mock LLM 의 수치는 취약성 측정값이 아니다.** mock 은 시나리오 작성자가 만든 규칙으로 동작하는 "순진한 지시 수행기"라서
  ASR 87% 같은 숫자는 하네스·채점·레일 배선이 맞게 돌아간다는 증거일 뿐이다. 강의에 쓸 수치는 `--llm openai` 로 다시 뽑아야 한다.
- `OpenAICompatLLM` 은 연구실 Ollama(`qwen2.5:7b`)로 전체 31건을 1회 돌려 요청 형식·tool_call 왕복·채점이 동작함을 확인했다(`results/baseline-qwen25-7b_*`).
  **그러나 그 수치(ASR 30%, 정상 업무 PASS 2/8)도 취약성 측정값이 아니다.** 7B 모델이 도구를 안 부르거나 엉뚱한 도구를 불러서,
  BLOCKED 상당수는 모델이 거절한 게 아니라 공격이 실행 단계에 못 간 것이고 정상 업무 FAIL 도 모델 탓이다(자세한 내용은 `docs/04`).
  GPT 등 도구 호출이 안정적인 모델로는 아직 돌려보지 않았다(연구실 codex-lb 키 미확보). 그 모델로 재실행하기 전까지 강의용 수치로 쓰지 않는다.
- 시나리오는 서로 독립이다. 오염 문서 d5/d7/d8 은 각각 A13/A16/A21 에서만 인덱스에 들어간다 (`extra_docs`). 처음엔 모든 시나리오에 넣었다가
  키워드 검색이 d5 를 엉뚱한 시나리오에 끌어와 결과가 오염되는 것을 확인하고 분리했다.
- 모든 데이터는 가상이다. 공격 문구는 OWASP LLM Top 10 교육용 수준이며 이 앱(로컬, 가짜 데이터) 밖에서는 동작하지 않는다.
