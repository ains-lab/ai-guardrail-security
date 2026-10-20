# 05. Udemy 대응표 — Step 1 공격 시나리오 구성 (2026-10-15)

캠퍼스 강의목차 **Step 1. 공격 시나리오 구성: OWASP Prompt Injection·권한 우회 등 주요 공격 케이스 설계** 를
Udemy 코스 기준으로 정리한 것이다.

- 코스: *AI Security & AI Guardrails : Agents, Red Teaming & Hands-On* (Firstlink Consulting)
  `udemy.com/course/ethical-secure-ai-guardrailsai-nvidia-nemo-guardrails/`
- 규모: 27개 섹션 / 135개 강의 / 9시간 5분 (2026-10 기준 최신 갱신본)

**확인 범위 (정직하게)**: 공개 강의 목차 페이지의 섹션·강의 **제목**을 모두 읽었고, Step 1 관련 섹션(§3, §7, ASI01~03, 05, 06)은
강의별 **설명문**(펼침 항목, 1~3문장)까지 읽었다. 설명문은 요약이라 실제 강의 내용과 다를 수 있다.
§6 에 설명문으로 확인한 사실과 그에 따른 정정을 적었다.

## 1. Step 1 에 쓰는 Udemy 섹션

| 우선순위 | Udemy 섹션 | 강의 (제목) | Step 1 에서의 쓰임 |
|---|---|---|---|
| 핵심 | §3 Input Guardrails: Prompt Injection (LLM01) · 5강 26분 | Prompt Injection: The Hidden Threat / Prompt Guard: Detecting Injection and Jailbreaks / Hands-On: Screen Prompts with Prompt Guard / Llama Guard: Policy-Based Input and Output Moderation / Hands-On: Moderate Conversations with Llama Guard | 직접 인젝션·탈옥 공격 유형 정의 (A01, A04) |
| 핵심 | §7 Red Teaming: Scan LLM Vulnerabilities with Garak · 9강 34분 | What Is AI Red Teaming? / Introduction to Garak / Garak Probes / Hands-On: Encoding Attacks / Data Exfiltration: How Sensitive Data Leaks Out / Hands-On: Data Exfiltration Probes / Hands-On: Profanity Probes 외 | 공격 카테고리 분류 틀 (인코딩·유출·유해 출력) (A12, A09, A15) |
| 핵심 | §17 ASI01 Agent Goal Hijack · 4강 | Scenario 1: Customer Service Refund Workflow Hijack / Technology Map: Indirect Prompt Injection and Trust Boundaries | 간접 인젝션과 신뢰 경계 (A13) |
| 핵심 | §18 ASI02 Tool Misuse & Exploitation · 4강 | Scenario 1: Refund Machine Loops Payouts / Technology Map: Execution Guardrails, Idempotency, and State Validation | 도구 남용·반복 호출 (A08, A14) |
| 핵심 | §19 ASI03 Identity & Privilege Abuse · 2강 7분 | Technology Map: Non-Human Identity, Trust Chains, and JIT Agency / Shared Defense Architecture: Task-Scoped Identity Controls | **권한 우회** 에 가장 가까운 섹션 (A06, A07). 시나리오 강의는 없고 개념·방어만 있음 |
| 보조 | §6 Data Guardrails: Protect PII with Presidio (LLM02) · 9강 | Your Data in Someone Else's Model / Hands-On: Detect PII with Presidio Analyzer 외 | PII 노출 시나리오 (A10) 및 정상 업무 B04 의 판정 기준 |
| 보조 | §21 ASI05 Unexpected Code Execution · 4강 | Overview: When Output Crosses the Data-to-Code Boundary / Scenario 1: The Self-Healing Disaster | 불안전한 출력 처리 (A11) |
| 보조 | §22 ASI06 Memory & Context Poisoning · 4강 | Scenario 1: The Travel Pricing Ghost / Technology Map: Retrieval Trust, Provenance, and Write Controls | RAG 오염 (A13, A05) |
| 배경 | §2 GenAI Foundations · 10강 | Prompts: Anatomy of a Prompt / Vector Embeddings and Semantic Search 외 | 팀 공통 배경지식. 시나리오 설계에는 직접 불필요 |
| 배경 | ASI 섹션 공통 구조 | Overview → Scenario 1 → Technology Map → Shared Defense Architecture | 우리 시나리오 설계서 양식(공격 → 약점 → 방어)과 같은 구조라 참고하기 좋음 |

섹션 번호는 목차 순서이며 Udemy 화면에 번호가 표기되는 것은 아니다.

## 2. 우리 시나리오 15건 ↔ Udemy

| 시나리오 | OWASP | Udemy 대응 | 비고 |
|---|---|---|---|
| A01 직접 프롬프트 인젝션 | LLM01, LLM02 | §3 | |
| A02 시스템 프롬프트 직접 요청 | LLM07 | **없음** | 제목 기준으로 LLM07 전용 강의 없음 |
| A03 시스템 프롬프트 간접 추출 | LLM07, LLM01 | §3 (인젝션 일반) | LLM07 은 위와 동일 |
| A04 롤플레이 탈옥 (DAN) | LLM01 | §3 (Prompt Guard 의 jailbreak 탐지) | |
| A05 RAG 접근제어 부재 | LLM08, LLM02 | ASI06 (Retrieval Trust, Write Controls) | 접근제어 자체보다 오염 관점 |
| A06 권한 사칭 | LLM01, LLM06 | ASI03 | |
| A07 도구 BOLA/IDOR | LLM06, LLM02 | ASI03 (Task-Scoped Identity) | 객체 단위 접근 통제 강의는 제목상 없음 |
| A08 SQL 도구 남용 | LLM06 | ASI02 | |
| A09 외부 유출 시도(직접) | LLM06, LLM02 | §7 Data Exfiltration | |
| A10 PII 노출 | LLM02 | §6 Presidio | |
| A11 불안전한 출력 처리 | LLM05 | ASI05 | |
| A12 base64 난독화 우회 | LLM01 | §7 Hands-On: Encoding Attacks | 1:1 로 맞는 강의 |
| A13 간접 인젝션(RAG poisoning) | LLM01, LLM04, LLM06 | ASI01 + ASI06 | |
| A14 무제한 소비 | LLM10 | ASI02 (Refund Machine Loops Payouts) | LLM10 전용은 없고 반복 실행 관점으로 근접 |
| A15 유해 콘텐츠 생성 | CONTENT-SAFETY | §7 Profanity Probes, §3 Llama Guard | |

정상 업무 B01~B06 은 Udemy 에 대응 강의가 없다. 다만 B06(문서에 없는 질문)은 §5 Output Guardrails: Hallucination &
Misinformation (LLM09) 와 같은 주제이고, B05(권한 있는 사용자 과차단 방지)는 코스에 해당 개념이 없는 우리 쪽 고유 항목이다.

## 3. 양쪽에서 비어 있는 부분

- **Udemy 에 있고 우리에 없음**: §4 멀티모달 이미지 인젝션(우리 앱은 텍스트 전용이라 제외 권장), ASI04 공급망, ASI07 에이전트 간 통신,
  ASI08 연쇄 장애, ASI09 인간-에이전트 신뢰, ASI10 Rogue Agents (우리 앱은 단일 에이전트라 해당 없음).
- **우리에 있고 Udemy 에 없음**: A02·A03(LLM07 시스템 프롬프트 유출), A05(RAG 접근제어), A07(BOLA). 이 항목은 Udemy 가 아니라
  OWASP LLM Top 10 2025 원문을 근거로 유지한다.
- Step 1 문구의 "권한 우회" 는 Udemy 에서 ASI03 2강뿐이라 가장 얕게 다뤄진다. 이쪽은 코스에 기대기보다 우리 시나리오(A06, A07)가 실질 근거다.

## 4. 보강 결과 (v0.2 반영 완료)

위 "비어 있는 부분" 중 이 앱에서 재현 가능한 것을 시나리오로 추가했다. 정의는 `asi/scenarios.json`(A22 는 `owasp/scenarios.json`) 의 `source` 필드.

| 신규 | Udemy 근거 | 내용 |
|---|---|---|
| A16 | ASI01 Agent Goal Hijack | 오염된 환불 절차 문서(d7)가 `UPDATE refunds` 실행을 지시 |
| A17 | ASI02 Tool Misuse | SELECT 만으로 `sqlite_master` 조회해 스키마 정찰 |
| A18 | ASI03 Identity & Privilege Abuse | 가짜 시스템 메시지로 role 이 hr_admin 이 됐다고 선언 |
| A19 | ASI03 (Trust Chains, JIT Agency) | 가짜 위임장·승인 번호 주장 |
| A20 | ASI05 (Data-to-Code Boundary) | 마크다운 이미지로 외부 요청 유발 |
| A21 | ASI06 Memory & Context Poisoning (+LLM09) | 지시문 없이 거짓 규정 문서(d8)만 심어 오답 유도 |
| A22 | Garak Encoding 프로브 | hex 인코딩 인젝션 |
| A23 | ASI02 Scenario 1 (Refund Machine Loops Payouts) | `issue_refund` 도구 추가, 완료 토큰 없이 같은 주문을 반복 지급 |
| B07 | ASI02 | 정상 SELECT 조회가 과차단되지 않는지 확인 |
| B08 | ASI02 | 정상 지급 1회가 과차단되지 않는지 확인 |

제외한 것: 이미지 인젝션(앱이 텍스트 전용), ASI04 공급망(플러그인 로딩 없음), ASI07~10(단일 에이전트), 멀티턴 공격(에이전트가 단일 턴).

## 5. 남은 일

1. ASI01·ASI02·ASI03 의 "Scenario 1" 강의를 직접 보고 공격 문구 수정이 필요한지 확인한다.
2. Step 3 평가는 Udemy 가 Haystack 평가자(Faithfulness / Context Relevance / SAS)를 쓰고 우리는 RAGAS 를 쓰는 점이 다르다. 지표 개념은 같다.

## 6. 강의 설명문으로 확인한 내용과 정정

| 섹션 | 설명문 요지 | 우리 시나리오와의 관계 |
|---|---|---|
| §3 Prompt Injection | 쇼핑 비서가 한 상품을 편애하도록 조종되는 예. 직접·간접 인젝션과 "일반 필터링이 왜 놓치는가". 나머지 4강은 Prompt Guard / Llama Guard **방어 도구** 실습 | 공격 설계보다 **방어 도구 소개** 비중이 큼. Step 1 공격 문구의 직접 근거는 첫 강의 1개뿐 |
| §7 Garak | Encoding Attacks: "Base64 등 인코딩 텍스트가 입력 필터를 통과하는지". Data Exfiltration: LLM 으로 민감 정보를 밖으로 빼는 방식. Profanity: 모델이 욕설을 내놓게 밀어붙이는지 | A12·A22(인코딩), A09·A13(유출), A15(유해 출력)와 **직접 대응** |
| ASI01 | 외부 입력이 추론 루프와 행동에 영향. 환불 워크플로에서 **신뢰할 수 없는 콘텐츠**를 읽는 상황 | A16 과 **잘 맞음** |
| ASI02 | "권한이 있는 정당한 도구를 잘못된 때·멈추는 조건 없이 써서 생기는 피해". 시나리오: 사기성 환불 요청이 **완료 토큰/멱등성 부재**로 반복 지급을 유발 | A14(반복 호출)와 가까움. **A17(스키마 정찰)은 이 설명과 다름** — 정찰은 Udemy 근거 없음, 우리가 추가한 변형 |
| ASI03 | 모호한 위임 범위와 긴 신뢰 사슬이 권한 남용을 만든다. 위임 단계마다 작업 범위 신원 검증 | A19(위임 사칭)와 **잘 맞음**. A18(가짜 시스템 메시지)은 ASI03 보다 LLM01 쪽 |
| ASI05 | 텍스트가 **shell / SQL / Python 실행**으로 넘어가는 경계 | 우리 앱에서는 `run_sql`(A08, A16)이 해당. **A20(마크다운 이미지)은 ASI05 가 아니다** — 출력 유출 경로로 LLM05 에 가깝다 |
| ASI06 | 가짜 운임이 가격 벡터 저장소에 심어져 조회 시 오염된 기억이 검색됨 | A21 과 **잘 맞음** (지시문 없이 거짓 값만 심는 구조) |

**정정**: A17, A20 의 `source` 를 "근접"으로 바꿨다. 두 시나리오는 이 앱의 약점(W4, W7)에는 맞지만 Udemy 해당 섹션의 설명과는 직접 대응하지 않는다.

**ASI02 핵심 시나리오 반영**: Udemy 의 "완료 토큰 없는 반복 지급(멱등성)"은 우리 앱에 지급 도구가 없어 처음엔 옮기지 못했다.
`issue_refund(order_id)` 도구와 지급 원장(`payouts`)을 추가해 A23 으로 구현했다 (약점 W11). Udemy 가 함께 다루는 "상태 검증"(이미 완료된
환불 재지급)과 "금액 상한"은 Rail 인터페이스가 DB 상태를 볼 수 없어 이번에는 만들지 않았다.
