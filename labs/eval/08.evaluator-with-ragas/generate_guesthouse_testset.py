# /// script
# requires-python = ">=3.12,<3.14"
# dependencies = ["ragas==0.4.3", "langchain-community==0.3.31", "langchain-openai==0.3.35"]
# ///
"""성동구 조사 보고서로 RAGAS single-hop 합성 평가셋 생성.

실행 (프로젝트 루트 또는 다른 경로):
  uv run --python 3.12 generate_guesthouse_testset.py --dry-run
  uv run --python 3.12 generate_guesthouse_testset.py --size 2

기본 LLM: http://127.0.0.1:8080/v1 의 qwen2.5-7b.
경량 single-hop 경로: Markdown 절을 KG 노드로 만들고 제목을 entities로 사용.
임베딩·기본 그래프 추출·multi-hop은 사용하지 않는다. 생성 결과는 법률 정답이
아니며 원문과 공식 출처를 기준으로 사람의 검수를 거쳐야 한다.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re

# 외부 분석/추적 전송은 기본 차단. 외부 LLM URL은 사용자가 명시할 때만 사용.
os.environ.setdefault("RAGAS_DO_NOT_TRACK", "true")
os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")
HERE = Path(__file__).resolve().parent
DEFAULT_SOURCE = HERE.parent / "research/seongdong-guesthouse-preparation.md"


def load_sections(path):
    text = path.read_text(encoding="utf-8")
    # 출처 목록/부록은 질문 문맥에서 제외. 원본 파일 hash로 추적한다.
    body = text.split("## 부록 A", 1)[0]
    chunks = []
    for part in re.split(r"(?=^## )", body, flags=re.MULTILINE):
        if not part.startswith("## "):
            continue
        title = part.splitlines()[0].removeprefix("## ").strip()
        if len(part.strip()) < 150:
            continue
        chunks.append((title, part.strip()))
    if not chunks:
        raise ValueError(f"사용할 Markdown 절이 없습니다: {path}")
    return text, chunks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=HERE / "outputs")
    parser.add_argument("--size", type=int, default=10)
    parser.add_argument("--base-url", default="http://127.0.0.1:8080/v1")
    parser.add_argument("--model", default="qwen2.5-7b")
    parser.add_argument("--dry-run", action="store_true", help="문서 로딩만 검사. LLM 호출/파일 저장 없음")
    args = parser.parse_args()
    if args.size < 1:
        parser.error("--size는 1 이상이어야 합니다.")
    text, sections = load_sections(args.source.resolve())
    print(f"입력: {args.source.resolve()} / 절: {len(sections)} / 요청 샘플: {args.size}")
    if args.dry_run:
        for title, content in sections:
            print(f"- {title}: {len(content)} characters")
        return
    from langchain_openai import ChatOpenAI
    from ragas.llms import LangchainLLMWrapper
    from ragas.run_config import RunConfig
    from ragas.testset import TestsetGenerator
    from ragas.testset.graph import KnowledgeGraph, Node, NodeType
    from ragas.testset.persona import Persona
    from ragas.testset.synthesizers.single_hop.specific import SingleHopSpecificQuerySynthesizer

    llm = LangchainLLMWrapper(ChatOpenAI(
        model=args.model, base_url=args.base_url,
        api_key=os.environ.get("RAGAS_API_KEY", "local-no-auth"),
        temperature=0, max_tokens=768, timeout=120, max_retries=1,
    ))
    kg = KnowledgeGraph(nodes=[Node(type=NodeType.CHUNK, properties={
        "page_content": content, "entities": [title],
        "document_metadata": {"source": str(args.source.resolve()), "section": title},
    }) for title, content in sections])
    synthesizer = SingleHopSpecificQuerySynthesizer(llm=llm)
    # 별도 번역 API를 호출하지 않고 생성 지시에 한국어를 지정한다.
    synthesizer.generate_query_reference_prompt.instruction += (
        "\n질문과 답변은 반드시 한국어로 작성하세요. 문맥에 없는 법적 요건을 추가하지 마세요. "
        "허가 가능성을 확정하지 말고 원문의 조건·예외·미확인 사항을 유지하세요."
    )
    generator = TestsetGenerator(
        llm=llm, embedding_model=None, knowledge_graph=kg,
        persona_list=[Persona(name="숙박업 준비자", role_description="성동구 자가 단독주택에서 비거주 상태로 내외국인 숙박영업을 준비하며 인허가와 사전 확인사항을 알고 싶다.")],
    )
    testset = generator.generate(
        testset_size=args.size, query_distribution=[(synthesizer, 1.0)],
        run_config=RunConfig(timeout=180, max_retries=1, max_workers=1),
        raise_exceptions=True,
    )
    rows = testset.to_pandas().to_dict(orient="records")
    if len(rows) != args.size:
        raise RuntimeError(f"샘플 수 불일치: 요청 {args.size}, 결과 {len(rows)}")
    for row in rows:
        for field in ("user_input", "reference", "reference_contexts"):
            if not row.get(field):
                raise ValueError(f"빈 필수 필드: {field}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    # 실행별 디렉터리로 이전 산출물 덮어쓰기 방지.
    from uuid import uuid4
    output = args.output_dir / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8])
    output.mkdir()
    testset.to_pandas().to_json(output / "testset.jsonl", orient="records", lines=True, force_ascii=False)
    testset.to_pandas().to_csv(output / "testset.csv", index=False)
    kg.save(str(output / "knowledge_graph.json"))
    metadata = {
        "source": str(args.source.resolve()), "source_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "model": args.model, "base_url": args.base_url, "ragas_version": importlib.metadata.version("ragas"),
        "samples": len(rows), "strategy": "single-hop / section-title entities / no embeddings",
        "human_review_required": True,
    }
    (output / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"생성 완료: {len(rows)}개 / {output.resolve()}")


if __name__ == "__main__":
    main()
