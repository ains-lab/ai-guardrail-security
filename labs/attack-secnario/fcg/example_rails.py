"""Rail 인터페이스 동작 확인용 예시 (Step 4 산출물이 아니다).

- build()      : 일부러 불완전한 최소 구성. 입력 필터 + 도구 정책 + 출력 정화
- build_full() : build() + 검색 ACL 필터 + 시스템 프롬프트 canary 출력 차단

Step 4 담당자는 이 파일을 참고해 Guardrails AI / NeMo Guardrails 를 Rail 안에 감싸면 된다.
"""
from __future__ import annotations

import re

from .data import CANARY_SYSPROMPT, COMPANY_DOMAIN
from .rails import Rail, RailContext, RailResult


class InputRegexRail(Rail):
    """키워드 기반 입력 필터. 인코딩/번역 우회에는 약하다는 점을 보여주는 용도."""
    name = "input_regex"
    _PATTERNS = re.compile(
        r"(이전|위의|기존|앞선)\s*(지시|명령|규칙|지침)\S*\s*(모두|전부)?\s*(무시|잊)"
        r"|ignore\s+(all\s+|any\s+)?(the\s+)?(previous|prior|above)\s+(instructions|rules)"
        r"|\bDAN\b|제한이\s*없|(인사팀|HR)\s*관리자|관리자\s*권한|시스템\s*프롬프트", re.I)

    def on_input(self, ctx: RailContext, text: str) -> RailResult:
        m = self._PATTERNS.search(text)
        return RailResult.block(f"suspicious pattern: {m.group(0)!r}") if m else RailResult.allow()


class ToolPolicyRail(Rail):
    """도구 실행 직전 정책 검사 (모델이 속아도 코드 레벨에서 막는다)."""
    name = "tool_policy"
    MAX_CALLS = 5

    def on_tool_call(self, ctx: RailContext, name: str, args: dict) -> RailResult:
        ctx.state["calls"] = ctx.state.get("calls", 0) + 1
        if ctx.state["calls"] > self.MAX_CALLS:
            return RailResult.block(f"tool call budget exceeded ({self.MAX_CALLS})")
        if name == "send_email" and not str(args.get("to", "")).lower().endswith("@" + COMPANY_DOMAIN):
            return RailResult.block("external recipient not allowed")
        if name == "run_sql" and not re.match(r"\s*select\b", str(args.get("query", "")), re.I):
            return RailResult.block("only SELECT is allowed")
        if name == "get_employee" and ctx.user["role"] != "hr_admin" and str(args.get("name", "")) != ctx.user["id"]:
            return RailResult.block("cannot read other employee's record")
        return RailResult.allow()


class OutputSanitizeRail(Rail):
    name = "output_sanitize"
    _SCRIPT = re.compile(r"<script.*?</script>", re.I | re.S)
    _PHONE = re.compile(r"01[016789]-\d{3,4}-\d{4}")
    _EMAIL = re.compile(r"[\w.+-]+@(?!" + re.escape(COMPANY_DOMAIN) + r")[\w-]+(?:\.[\w-]+)+")
    _TOXIC = re.compile(r"멍청|바보")

    def on_output(self, ctx: RailContext, text: str) -> RailResult:
        if self._TOXIC.search(text):
            return RailResult.block("toxic content")
        cleaned = self._SCRIPT.sub("[removed script]", text)
        cleaned = self._PHONE.sub("[masked phone]", cleaned)
        cleaned = self._EMAIL.sub("[masked email]", cleaned)
        return RailResult.rewrite(cleaned, "sanitized") if cleaned != text else RailResult.allow()


class AclRetrievalRail(Rail):
    """검색된 문서를 사용자 role 기준으로 필터링 (Step 2 에서 발견될 W1 대응)."""
    name = "acl_retrieval"

    def on_retrieval(self, ctx: RailContext, query: str, docs: list) -> list:
        return [d for d in docs if ctx.user["role"] in d["allowed_roles"]]


class PromptCanaryRail(Rail):
    name = "prompt_canary"

    def on_output(self, ctx: RailContext, text: str) -> RailResult:
        return RailResult.block("system prompt leak") if CANARY_SYSPROMPT in text else RailResult.allow()


def build() -> list:
    return [InputRegexRail(), ToolPolicyRail(), OutputSanitizeRail()]


def build_full() -> list:
    return build() + [AclRetrievalRail(), PromptCanaryRail()]
