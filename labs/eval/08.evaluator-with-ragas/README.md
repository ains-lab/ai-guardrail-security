# RAGAS 합성 데이터 생성과 평가

프로젝트 루트에서 실행한다. 로컬 llama.cpp의 `http://127.0.0.1:8080/v1`에 `qwen2.5-7b`가 실행 중이어야 한다. uv는 각 스크립트의 고정된 의존성을 별도 환경에 설치한다. 프로젝트 .venv에 ragas를 설치할 필요가 없다.

## 합성 데이터

```bash
uv run --python 3.12 labs/eval/08.evaluator-with-ragas/generate_guesthouse_testset.py --size 10
```

`outputs/<실행ID>/testset.jsonl`에 질문, 합성 참조답변, 참조 문맥이 저장된다. 법률 정답으로 사용하기 전에 검수해야 한다.

## 평가

```bash
# 최신 합성 데이터셋의 전체 행 평가
uv run --python 3.12 labs/eval/08.evaluator-with-ragas/evaluate_guesthouse.py

# 요청 없이 입력/검색 확인
uv run --python 3.12 labs/eval/08.evaluator-with-ragas/evaluate_guesthouse.py --dry-run

# 초기 실행은 1개만 평가
uv run --python 3.12 labs/eval/08.evaluator-with-ragas/evaluate_guesthouse.py --limit 1
```

`--dataset <testset.jsonl>`로 특정 생성본, `--source <보고서.md>`로 검색 문서, `--top-k 1`로 검색할 절 개수를 지정한다. 별도 심판 모델이 있으면 `--judge-base-url`과 `--judge-model`을 지정할 수 있다. 실제 키는 `RAGAS_API_KEY`, `RAGAS_JUDGE_API_KEY` 환경 변수로만 전달한다. 기본 로컬 서버는 인증이 없어 공개 더미 값을 사용한다. 외부 endpoint를 지정하면 문서와 응답이 해당 공급자에게 전송된다.

## 처리 흐름

```text
합성 질문 → 보고서 절의 문자 bigram 검색 → Qwen 실제 답변 생성
        → RAGAS가 검색 문맥·실제 답변·합성 참조답변 비교 → 점수 저장
```

검색은 작은 실습용 lexical baseline이며 벡터 DB가 아니다. 참조답변과 참조문맥은 답변 생성 입력에 전달하지 않는다. 다만 합성 데이터와 검색 자료가 같은 보고서이므로 독립적인 법률 검증은 아니다.

| 지표 | 비교 내용 |
| --- | --- |
| faithfulness | 답변 주장이 검색 문맥으로 뒷받침되는지 |
| llm_context_precision_with_reference | 검색 순서에서 참조답변에 유용한 문맥이 우선되는지 |
| context_recall | 참조답변의 내용을 검색 문맥이 얼마나 뒷받침하는지 |
| factual_correctness | 실제 답변과 참조답변의 주장 단위 F1 일치도 |

0~1 점수로 저장한다. FactualCorrectness는 법률의 객관적 진실이 아니라 주어진 합성 참조답변과의 일치도다. Faithfulness가 높아도 답변이 참조답변을 충분히 포함하지 않으면 FactualCorrectness가 낮을 수 있다. top-k=1인 문맥 정밀도는 검색 순위 성능 전체를 설명하지 못한다.

## 결과 확인

`evaluations/<실행ID>/`에 다음을 저장하고 콘솔에 요약을 출력한다.

- `samples.jsonl`: 질문·실제 답변·검색 문맥·참조답변. 평가 호출 전에 저장한다.
- `scores.jsonl`, `scores.csv`: 행별 점수와 입력. CSV로 문항별 결과를 비교할 수 있다.
- `summary.json`: 지표별 평균·유효 평가 수·실패/미정 수, 모델·endpoint·원문/데이터 hash 등.

실패/미정 점수는 0점으로 바꾸지 않으며 평균에서 제외하고 별도 개수를 기록한다. 일부 지표라도 미정이면 결과 저장 후 비정상 종료하여 알린다. 실패가 없더라도 점수가 충분한지 판단하는 통과 기준은 별도로 정해야 한다.

## 실제 실행 기록

샘플 1개로 전 과정을 실행했다. 결과 디렉터리:
`evaluations/20261020T193539Z-10a39722/`

| 지표 | 관측 점수 | 유효 / 미정 |
| --- | --- | --- |
| faithfulness | 0.9230769230769231 | 1 / 0 |
| llm_context_precision_with_reference | 0.9999999999 | 1 / 0 |
| context_recall | 1.0 | 1 / 0 |
| factual_correctness | 0.24 | 1 / 0 |

이 기록은 1문항의 실행 확인이지 전체 시스템 품질의 통계적 결론이 아니다. 합성 생성·답변·심판이 같은 Qwen이므로 공유 편향이 존재한다. 더 많은 검수 문항과 독립된 심판 모델로 재평가할 것을 권장한다.

RAGAS 0.4.3의 검증된 레거시 `evaluate`/metric 및 LangchainLLMWrapper API를 사용하므로 deprecation 경고가 나온다. 현재 버전에서 실행은 확인했으며 향후 버전 호환성을 보장하지 않는다. 임베딩이 필요한 AnswerRelevancy/SemanticSimilarity는 이번 경량 로컬 평가에서 제외했다.
