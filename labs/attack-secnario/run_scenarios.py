"""시나리오 실행기.

  python run_scenarios.py --label baseline
  python run_scenarios.py --label hardened --rails fcg.example_rails:build
  python run_scenarios.py --compare results/baseline_results.json results/hardened_results.json
  python run_scenarios.py --llm openai --model gpt-4o-mini --label baseline-gpt   (FCG_API_KEY 또는 OPENAI_API_KEY 필요)
"""
from __future__ import annotations

import argparse
import base64
import importlib
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path

from fcg.agent import Agent
from fcg.data import USERS
from fcg.judge import evaluate
from fcg.llm import MockVulnerableLLM, OpenAICompatLLM

ROOT = Path(__file__).parent


def expand(text: str) -> str:
    text = re.sub(r"\{\{b64:(.*?)\}\}", lambda m: base64.b64encode(m.group(1).encode("utf-8")).decode("ascii"), text)
    return re.sub(r"\{\{hex:(.*?)\}\}", lambda m: m.group(1).encode("utf-8").hex(), text)


def load_rails(spec: str | None) -> list:
    if not spec:
        return []
    mod, _, fn = spec.partition(":")
    return getattr(importlib.import_module(mod), fn or "build")()


def run_all(args) -> dict:
    scenarios = json.loads(Path(args.scenarios).read_text(encoding="utf-8"))["scenarios"]
    if args.only:
        wanted = set(args.only.split(","))
        scenarios = [s for s in scenarios if s["id"] in wanted]
    llm = MockVulnerableLLM() if args.llm == "mock" else OpenAICompatLLM(model=args.model)
    rails = load_rails(args.rails)
    results = []
    for scn in scenarios:
        agent = Agent(llm, rails=rails)  # 시나리오마다 독립 실행(상태 공유 없음)
        trace = agent.run(expand(scn["input"]), USERS[scn["user"]], scenario_id=scn["id"],
                          extra_docs=tuple(scn.get("extra_docs", [])))
        ev = evaluate(scn, trace)
        results.append({"id": scn["id"], "kind": scn["kind"], "track": scn["track"], "title": scn["title"],
                        "owasp": scn.get("owasp", []), **ev, "trace": trace.to_dict(),
                        "contexts": [d["text"] for d in trace.retrieved], "reference": scn.get("reference", "")})
        if args.verbose:
            print(json.dumps(results[-1], ensure_ascii=False, indent=2))
    return {"label": args.label, "llm": args.llm if args.llm == "mock" else f"{args.llm}:{llm.model}",
            "rails": args.rails or "none", "results": results}


def summarize(run: dict) -> dict:
    atk = [r for r in run["results"] if r["kind"] == "attack"]
    ben = [r for r in run["results"] if r["kind"] == "benign"]
    count = lambda rs, o: sum(1 for r in rs if r["outcome"] == o)
    by_owasp: "OrderedDict[str, list]" = OrderedDict()
    for r in atk:
        for tag in r["owasp"]:
            by_owasp.setdefault(tag, []).append(r)
    return {
        "attack_total": len(atk), "exploited": count(atk, "EXPLOITED"), "exposed": count(atk, "EXPOSED"),
        "blocked": count(atk, "BLOCKED"),
        "asr": round(count(atk, "EXPLOITED") / len(atk), 3) if atk else 0.0,
        "benign_total": len(ben), "benign_pass": count(ben, "PASS"),
        "by_owasp": {k: {"total": len(v), "exploited": count(v, "EXPLOITED")} for k, v in sorted(by_owasp.items())},
    }


def render_report(run: dict) -> str:
    s = summarize(run)
    L = [f"# 시나리오 실행 결과: {run['label']}", "",
         f"- LLM: `{run['llm']}` / Rails: `{run['rails']}`",
         f"- 공격 {s['attack_total']}건: EXPLOITED {s['exploited']} / EXPOSED {s['exposed']} / BLOCKED {s['blocked']}"
         f"  (ASR = {s['asr']:.0%})",
         f"- 정상 업무 {s['benign_total']}건: PASS {s['benign_pass']}", "",
         "| ID | 유형 | OWASP | 결과 | 근거 | 레일 개입 |", "|---|---|---|---|---|---|"]
    for r in run["results"]:
        ev = r["trace"]["rail_events"]
        rails = ", ".join(sorted({f"{e['stage']}:{e['rail']}" for e in ev})) or "-"
        why = ", ".join(r["matched"]) if r["kind"] == "attack" else (", ".join(r.get("failed", [])) or "-")
        L.append(f"| {r['id']} | {r['title']} | {','.join(r['owasp']) or '-'} | **{r['outcome']}** | {why or '-'} | {rails} |")
    L += ["", "## OWASP 항목별 (공격 건수 / EXPLOITED)", "", "| 항목 | 건수 | EXPLOITED |", "|---|---|---|"]
    L += [f"| {k} | {v['total']} | {v['exploited']} |" for k, v in s["by_owasp"].items()]
    return "\n".join(L) + "\n"


def compare(a_path: str, b_path: str) -> str:
    a, b = (json.loads(Path(p).read_text(encoding="utf-8")) for p in (a_path, b_path))
    bi = {r["id"]: r for r in b["results"]}
    L = [f"# Before/After: {a['label']} -> {b['label']}", "",
         "| ID | 제목 | Before | After | 변화 |", "|---|---|---|---|---|"]
    regress = []
    for r in a["results"]:
        o2 = bi[r["id"]]["outcome"]
        change = ""
        if r["kind"] == "attack" and r["outcome"] != "BLOCKED" and o2 == "BLOCKED":
            change = "차단됨"
        elif r["kind"] == "attack" and r["outcome"] == o2 and o2 != "BLOCKED":
            change = "여전히 뚫림"
        elif r["kind"] == "attack" and r["outcome"] == "EXPLOITED" and o2 == "EXPOSED":
            change = "부분 완화 (실행은 막았으나 데이터 노출 잔존)"
        elif r["kind"] == "benign" and r["outcome"] == "PASS" and o2 == "FAIL":
            change = "과차단(회귀)"
            regress.append(r["id"])
        L.append(f"| {r['id']} | {r['title']} | {r['outcome']} | {o2} | {change} |")
    sa, sb = summarize(a), summarize(b)
    L += ["", f"- 공격 성공률(ASR): {sa['asr']:.0%} -> {sb['asr']:.0%}  (EXPLOITED {sa['exploited']} -> {sb['exploited']}, "
              f"EXPOSED {sa['exposed']} -> {sb['exposed']})",
          f"- 정상 업무: PASS {sa['benign_pass']}/{sa['benign_total']} -> {sb['benign_pass']}/{sb['benign_total']}"
          + (f"  ⚠ 회귀: {', '.join(regress)}" if regress else "")]
    return "\n".join(L) + "\n"


def export_ragas(run: dict, path: Path) -> int:
    """Step 3 입력용. RAGAS 신/구 필드명을 모두 채운다. 검색 결과가 있는 실행만 내보낸다."""
    n = 0
    with path.open("w", encoding="utf-8") as f:
        for r in run["results"]:
            if not r["contexts"]:
                continue
            row = {"scenario_id": r["id"], "kind": r["kind"],
                   "user_input": r["trace"]["effective_input"], "retrieved_contexts": r["contexts"],
                   "response": r["trace"]["answer"], "reference": r["reference"],
                   "question": r["trace"]["effective_input"], "contexts": r["contexts"],
                   "answer": r["trace"]["answer"], "ground_truth": r["reference"]}
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    return n


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("--label", default="baseline")
    p.add_argument("--llm", choices=["mock", "openai"], default="mock")
    p.add_argument("--model", default=None)
    p.add_argument("--rails", default=None, help="module:factory (Rail 리스트를 반환)")
    p.add_argument("--scenarios", default=str(ROOT / "scenarios" / "scenarios.json"))
    p.add_argument("--only", default=None, help="콤마 구분 시나리오 ID")
    p.add_argument("--out", default=str(ROOT / "results"))
    p.add_argument("--compare", nargs=2, metavar=("BEFORE", "AFTER"))
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()

    if args.compare:
        print(compare(*args.compare))
        return 0

    run = run_all(args)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{args.label}_results.json").write_text(json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8")
    report = render_report(run)
    (out / f"{args.label}_report.md").write_text(report, encoding="utf-8")
    n = export_ragas(run, out / f"{args.label}_ragas.jsonl")
    print(report)
    print(f"saved: {out / (args.label + '_results.json')} (+ _report.md, _ragas.jsonl rows={n})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
