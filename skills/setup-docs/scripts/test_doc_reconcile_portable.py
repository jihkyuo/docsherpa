from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent.parent / "doc-reconcile" / "SKILL.md"

# 명백한 second-brain 도메인 리터럴 + phantom 트리거 문자열 (큐레이팅 — 일반 doc명 SPEC.md 등은 제외)
FORBIDDEN = [
    "bge-m3", "edge type", "config.py", "text-embedding-3-large",
    "confidentiality", "second-brain", "pre-commit docs-impact",
    "voice firewall", "synthesized thought",
]


def test_no_domain_literals():
    text = SKILL.read_text(encoding="utf-8")
    hits = [w for w in FORBIDDEN if w in text]
    assert hits == [], f"정본 doc-reconcile에 도메인 리터럴 누출: {hits}"


def test_references_language_agnostic_markers():
    text = SKILL.read_text(encoding="utf-8")
    assert "docsherpa:routing" in text, "라우팅 마커 참조 없음(헤딩 문자열 의존 의심)"
    assert "docsherpa:index" in text, "인덱스 마커 참조 없음"


def test_anchor_block_is_delimited_for_specialization():
    # §7.5: setup-docs가 특화할 앵커 블록이 경계 마커로 명확히 구분돼 있어야 한다.
    text = SKILL.read_text(encoding="utf-8")
    assert "docsherpa:anchors:start" in text and "docsherpa:anchors:end" in text, \
        "앵커 특화 경계 마커 없음 — §7.5 특화 대상이 불명확"
    start = text.index("docsherpa:anchors:start")
    end = text.index("docsherpa:anchors:end")
    assert start < end, "앵커 경계 마커 순서가 뒤바뀜"
