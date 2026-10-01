# AI Guardrails & AI Security — 강의 커리큘럼

- **원 강의:** AI Guardrails & AI Security - AI Agents, Red Teaming HandsOn
- **출처:** https://www.udemy.com/course/ethical-secure-ai-guardrailsai-nvidia-nemo-guardrails/?couponCode=26BBPPLO2MXTRMT
- **독자:** Python 기초를 아는 대학생. AI 보안이나 가드레일 도구를 처음 접해도 읽을 수 있도록 설명한다.
- **문서 범위:** 원 강의 공개 페이지에서 확인한 커리큘럼만 정리한다. 별도의 과제, 평가 기준, 실습 폴더 설계 또는 새로운 수업은 추가하지 않는다.

> **추출 상태: 부분 추출.** Udemy의 보안 확인으로 전체 섹션과 개별 강의 목록을 확보하지 못했다. 요청 URL의 추출 결과에는 29개 섹션·127개 강의·8시간 56분으로 표시되지만, 다른 조회 결과에는 18개 섹션·94개 강의로 나타나 총계의 최신성도 확정하지 않는다. 아래 A는 실제 `Course content`에서 확인한 항목이며, B와 C는 공개 강의 소개에 명시된 내용이다. 이 문서는 전체 강의 목록의 완전한 복제본이 아니다.

## A. 실제 강의 목록에서 확인된 내용

원문 제목을 함께 적어 Udemy에서 해당 항목을 찾을 수 있게 했다. 일부 섹션은 강의 제목이 누락되어 있으며, 아래 순서가 전체 섹션이 빠짐없이 이어지는 순서라는 의미는 아니다. 각 설명은 확인된 주제를 대학생 눈높이로 풀어 쓴 것이다.

### Introduction — 강의 소개

- **Welcome to AI Guardrails:** 생성형 AI 서비스의 전체 구조를 살펴보고, 입력과 출력의 어느 위치에 안전장치를 적용하는지 알아본다.
- **Course Contents:** 언어 모델, 검색 증강 생성, 입력 보호, 가드레일 프레임워크와 클라우드 적용 등 강의에서 다룰 범위를 살펴본다.

### General Concepts — 기본 개념

- **10,000 Foot view on Language Models:** BERT와 LLM 등 모델의 종류와 발전 흐름을 살펴본다. 미세 조정, 지도 미세 조정(SFT), 사람의 피드백을 이용한 강화학습(RLHF)의 기본 개념을 접한다.
- **LLM Inference Parameters:** 답변의 다양성과 길이를 조절하는 temperature, top_k, top_p, 응답 길이, 중단 시퀀스, 페널티를 배운다.
- **Vector Embedding:** 문장의 의미를 숫자 벡터로 나타내고, 벡터 사이의 거리를 이용해 의미가 비슷한 내용을 찾는 방법을 배운다.
- **RAG - Retrieval Augment Generation:** 답변을 만들기 전에 관련 자료를 검색해 참고하는 RAG를 이해한다. 자료를 찾아 읽고 답안을 작성하는 오픈북 시험과 비슷한 흐름이다.

### Large Language Models — 언어 모델의 한계

이 섹션의 전체 개별 강의 목록은 확보하지 못했다. 확인된 항목은 다음과 같다.

- **LLM Constraints - Bias and Ethical Concerns:** AI 답변의 편향과 공정성, 투명성, 책임 등 윤리 문제를 살펴본다.
- **LLM Constraints - Data Privacy and Security:** 개인정보나 민감한 데이터가 답변에 노출되는 위험과 보호의 필요성을 이해한다.
- **LLM Constraints – Output Alignment:** AI 답변이 서비스의 목적과 조직의 정책에서 벗어나지 않도록 맞추는 개념을 배운다.
- **Understanding Constraints in Large Language Models:** 언어 모델의 제약을 정리한다. 공개 추출 결과만으로는 이 항목이 영상인지 퀴즈인지 확인되지 않았다.

### AI Guardrails — AI 안전장치

- **Introduction to AI Guardrails:** AI에 들어오는 요청과 AI가 만든 답변을 검사하는 필터와 규칙을 이해한다.
- **Applications of AI Guardrails:** 전자상거래, 정신 건강, 법률, 여행 등의 서비스에서 가드레일을 어떻게 활용하는지 살펴본다.
- **Understand AI Guardrails:** 가드레일 개념을 정리한다. 공개 추출 결과만으로는 이 항목이 영상인지 퀴즈인지 확인되지 않았다.

### LLM01 OWASP - Prompt Injection — 프롬프트 인젝션

전체 개별 강의 목록은 확보하지 못했다.

- **Hands on with prompt-guard model:** Prompt Guard 모델을 사용해 악의적인 지시나 삽입된 명령을 탐지하는 실습을 한다. 프롬프트 인젝션은 AI가 따라야 할 원래 지시 대신 공격자가 넣은 지시를 따르게 유도하는 공격이다.

### Multimodel Guardrails — 텍스트와 이미지를 다루는 안전장치

`Multimodel Guardrails`는 공개 페이지에 표시된 섹션 제목을 그대로 보존했다.

- **Llama Guard 3 - Vision Theory:** 텍스트와 이미지를 함께 검사하는 모델의 종류, 입력 형식, 안전성 분류를 배운다.
- **Hands On with Llama Guard 3 - Vision:** 이미지가 포함된 입력의 안전성을 검사하는 실습을 한다.

### Scan LLM Vulnerability - Red Teaming — LLM 취약점 탐색

전체 개별 강의 목록은 확보하지 못했다.

- **Detect LLM Vulnerability - Encoding:** 문자를 인코딩하는 등 입력 표현을 바꾸어 안전 필터가 우회되는지 검사한다.
- **XFilteration:** 정보 유출 관련 취약점을 탐색하는 항목이다. 제목은 원문의 표기를 유지했다.

### 소속 섹션을 확인하지 못한 개별 항목

- **Llama Guard Prompt:** Llama Guard에 전달하는 프롬프트 형식을 다룬다. 공개 추출 결과에 제목은 있었지만 섹션 경계를 확인할 수 없어 별도로 기록했다.

## B. 공개 강의 소개에 명시된 학습 주제

아래는 실제 섹션 제목이나 수업 순서를 복원한 목록이 아니다. `What you'll learn`과 `Description`에 명시된 주제를 영역별로 정리한 것이다.

### 입력 보안과 콘텐츠 검사

- **프롬프트 인젝션 탐지:** Prompt Guard를 사용해 모델의 원래 지시를 바꾸려는 입력을 탐지한다.
- **콘텐츠 모더레이션:** 혐오, 폭력 등 정책에 어긋나는 입력을 분류한다.
- **Llama Guard 3:** 텍스트와 이미지 입력에 대한 안전성 분류를 다룬다.
- **NeMo Guardrails:** 대화의 의도와 흐름을 관리하고 제한된 요청을 처리하는 방법을 배운다.

### 출력 검증과 환각 탐지

- **환각(Hallucination):** AI가 근거 없는 내용을 사실처럼 답하는 현상을 이해한다.
- **phi3-hallucination-judge:** 생성한 답변의 환각 여부를 판단하는 모델을 활용한다.
- **GuardrailsAI Validators:** 출력이 정책이나 형식에 맞는지 검사하는 검증기를 사용한다. 개인정보(PII)와 금지 주제에 관한 정책도 다룬다.
- **RAIL 명세:** 출력 구조와 검증 규칙, 검증 실패 시의 처리 방식을 정의한다.
- **LLM-as-a-Judge:** 다른 언어 모델을 평가자로 사용해 답변이나 문맥의 적절성을 판단한다. 이는 모델의 평가이며, 사실 여부를 보장하는 판정은 아니다.

### RAG와 답변 품질 평가

- **벡터 저장소와 RAG:** 문서를 검색하고 검색한 내용을 근거로 답변을 생성하는 구조를 배운다.
- **Haystack Pipeline:** 검색과 생성 등의 단계를 연결하는 처리 흐름을 구성한다.
- **Faithfulness Evaluator:** 답변이 제공된 근거 자료에서 벗어나지 않았는지 평가한다.
- **SAS Evaluator:** 두 답변이 표현은 달라도 의미상 얼마나 비슷한지 평가한다.
- **Context Relevance Evaluator:** 검색한 문맥이 질문에 얼마나 관련 있는지 평가한다.
- **RAGAS Evaluator:** RAG 시스템의 검색과 답변 품질을 평가하는 도구를 다룬다.
- **FastRAG:** 검색 증강 생성 파이프라인을 다룬다.

### 클라우드와 가드레일 프레임워크

- **AWS Bedrock Guardrails:** 클라우드에서 콘텐츠 정책을 설정하고 가드레일을 배포·실행한다. 이미지 관련 가드레일도 다룬다.
- **NeMo Guardrails 적용:** 의도 분류 흐름과 사용자 정의 검증기를 연결한다.
- **GuardrailsAI 적용:** 출력 형식 검증과 정책 위반 시의 처리 방식을 구성한다.
- **Hugging Face와 Colab:** 공개 모델과 노트북을 활용하는 실습을 진행한다.

### 레드팀과 보안 스캔

- **Garak:** LLM에 다양한 시험 입력을 보내 취약한 반응이 나오는지 검사한다.
- **Encoding Probes:** 인코딩된 입력을 이용한 우회를 시험한다.
- **XFilteration Probes:** 정보 유출 관련 취약점을 탐색한다.
- **Profanity Probes:** 부적절한 표현을 생성하는지 검사한다.
- **CrewAI + OWASP ZAP:** AI 에이전트와 웹 보안 도구를 연결해 웹 취약점 탐색과 스캔 자동화를 다룬다. 이는 LLM 출력 안전성 검사와 구분되는 웹 애플리케이션 보안 영역이다.
- **다중 에이전트 위협 탐색:** 여러 에이전트가 보안 탐색에 참여하는 구성을 다룬다.

### 멀티모달과 에이전트 안전성

- **ReAct Architecture:** 추론과 도구 사용을 연결해 여러 단계로 작업하는 구조를 이해한다.
- **Phi-3.5-vision-instruct:** 이미지와 텍스트를 함께 다루는 모델을 활용한다.
- **영양 분석 사례와 준수 검사:** 공개 강의 소개에 제시된 사례를 통해 모델 활용과 정책 준수 검사를 살펴본다.

## C. 공개 강의 소개에 명시된 실습 프로젝트

| 원문 프로젝트명 | 대학생을 위한 설명 |
| --- | --- |
| Nemo Intent Firewall | 챗봇이 요청의 의도를 구분하고 제한된 질문을 차단하도록 구성한다. |
| GuardrailsAI HIPAA Enforcer | 개인정보를 가리고 금지 주제를 제한하는 정책을 적용한다. 프로젝트 제목에 HIPAA가 포함되어 있지만, 이 실습만으로 법적 준수가 입증되는 것은 아니다. |
| CrewAI Web Vulnerability Scanner | CrewAI와 웹 보안 도구를 이용해 XSS·SQL 인젝션 등의 취약점 탐색을 자동화한다. |
| Multimodal Jailbreak Detector | 텍스트뿐 아니라 이미지를 이용한 부적절한 입력과 안전장치 우회 시도를 탐지한다. |
| RAG Audit Dashboard | SAS 등 평가 지표를 사용해 RAG 답변의 품질을 살펴보는 대시보드를 다룬다. 의미 유사도와 근거 충실성은 구분해서 이해한다. |

---

**남아 있는 원문 확인:** 전체 섹션명, 모든 개별 강의 제목, 정확한 순서와 총계. Udemy의 ‘전체 섹션 펼치기’ 결과나 커리큘럼 내보내기 자료가 확보되면 A를 완전한 목록으로 대체할 수 있다.
