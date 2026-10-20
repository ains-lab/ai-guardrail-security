"""Step 3: RAGAS 평가 (Faithfulness, Context Relevance).

사전 준비 (Python 3.11/3.12 권장. 3.14 에서는 의존성 scikit-network 빌드가 실패했다):
    pip install -r requirements-ragas.txt
    $env:FCG_API_KEY = "sk-..."          # 판정용 LLM (OpenAI 호환). 로컬 Ollama 면 FCG_BASE_URL 도 지정

실행:
    python eval_ragas.py --input results/baseline_ragas.jsonl --model gpt-4o-mini
    python eval_ragas.py --input results/baseline_ragas.jsonl --dry-run     # 입력/지표 구성만 점검, LLM 호출 없음

ragas 0.4.3 기준 (`ragas.metrics.collections`). 지표 API 는 버전마다 달라서 다른 버전에서는 수정이 필요할 수 있다.
주의: 판정자도 LLM 이므로 공격 시나리오의 응답(거절문 등)은 Faithfulness 가 낮게 나올 수 있다. 정상 업무(B) 위주로 해석할 것.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import sys
from pathlib import Path


def load_rows(path: str) -> list:
    rows = [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]
    return [r for r in rows if r["response"] and r["retrieved_contexts"]]  # ragas 는 빈 응답/컨텍스트를 거부한다


async def score_all(rows: list, model: str, concurrency: int) -> list:
    from openai import AsyncOpenAI
    from ragas.llms import llm_factory
    from ragas.metrics.collections import ContextRelevance, Faithfulness

    client = AsyncOpenAI(api_key=os.environ.get("FCG_API_KEY") or os.environ.get("OPENAI_API_KEY", "none"),
                         base_url=os.environ.get("FCG_BASE_URL") or None)
    llm = llm_factory(model, client=client)
    faith, ctxrel = Faithfulness(llm=llm), ContextRelevance(llm=llm)
    sem = asyncio.Semaphore(concurrency)

    async def one(r: dict) -> dict:
        async with sem:
            out = {"scenario_id": r["scenario_id"], "kind": r["kind"]}
            for name, coro in (
                ("faithfulness", faith.ascore(user_input=r["user_input"], response=r["response"],
                                               retrieved_contexts=r["retrieved_contexts"])),
                ("context_relevance", ctxrel.ascore(user_input=r["user_input"],
                                                     retrieved_contexts=r["retrieved_contexts"])),
            ):
                try:
                    out[name] = float((await coro).value)
                except Exception as e:  # 한 건 실패가 전체를 멈추지 않게
                    out[name], out[name + "_error"] = None, repr(e)[:200]
            return out

    return await asyncio.gather(*(one(r) for r in rows))


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--model", default=os.environ.get("FCG_MODEL", "gpt-4o-mini"))
    p.add_argument("--concurrency", type=int, default=4)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    rows = load_rows(args.input)
    print(f"평가 대상 {len(rows)}건: " + ", ".join(r["scenario_id"] for r in rows))
    if args.dry_run:
        from ragas.metrics.collections import ContextRelevance, Faithfulness  # noqa: F401  (import 가능 여부 확인)
        print("dry-run: 입력 형식과 ragas 지표 import 확인 완료. LLM 은 호출하지 않았다.")
        return 0

    results = asyncio.run(score_all(rows, args.model, args.concurrency))
    out = Path(args.input).with_name(Path(args.input).stem.replace("_ragas", "") + "_ragas_scores.json")
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n| ID | 유형 | Faithfulness | Context Relevance |\n|---|---|---|---|")
    fmt = lambda v: "-" if v is None else f"{v:.2f}"
    for r in results:
        print(f"| {r['scenario_id']} | {r['kind']} | {fmt(r['faithfulness'])} | {fmt(r['context_relevance'])} |")
    for kind in ("benign", "attack"):
        for m in ("faithfulness", "context_relevance"):
            vals = [r[m] for r in results if r["kind"] == kind and r[m] is not None]
            if vals:
                print(f"평균 {kind:6s} {m}: {statistics.mean(vals):.2f} (n={len(vals)})")
    print(f"saved: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
