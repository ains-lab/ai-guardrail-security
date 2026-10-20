"""Guardrail 삽입 지점 (Step 4 인터페이스).

에이전트는 4곳에서 Rail을 호출한다. Guardrails AI / NeMo Guardrails / 직접 만든 규칙 어느 쪽이든
Rail 서브클래스 안에서 감싸서 쓰면 되고, `--rails 모듈:팩토리함수` 로 하네스에 꽂는다.

    on_input      사용자 입력이 LLM에 들어가기 전
    on_retrieval  검색된 문서가 LLM 컨텍스트에 들어가기 전 (반환: 통과시킬 문서 목록)
    on_tool_call  LLM이 요청한 도구를 실행하기 직전
    on_output     최종 답변이 사용자에게 나가기 전
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RailContext:
    user: dict
    scenario_id: str = ""
    events: list = field(default_factory=list)  # Trace.rail_events 와 공유
    state: dict = field(default_factory=dict)   # 실행 1건 동안만 유지되는 레일용 저장소 (예: 호출 횟수)


@dataclass
class RailResult:
    action: str = "allow"  # allow | block | rewrite
    text: str = ""         # rewrite 시 대체 텍스트
    reason: str = ""

    @classmethod
    def allow(cls) -> "RailResult":
        return cls("allow")

    @classmethod
    def block(cls, reason: str) -> "RailResult":
        return cls("block", reason=reason)

    @classmethod
    def rewrite(cls, text: str, reason: str) -> "RailResult":
        return cls("rewrite", text=text, reason=reason)


class Rail:
    name = "rail"

    def on_input(self, ctx: RailContext, text: str) -> RailResult:
        return RailResult.allow()

    def on_retrieval(self, ctx: RailContext, query: str, docs: list) -> list:
        return docs

    def on_tool_call(self, ctx: RailContext, name: str, args: dict) -> RailResult:
        return RailResult.allow()

    def on_output(self, ctx: RailContext, text: str) -> RailResult:
        return RailResult.allow()
