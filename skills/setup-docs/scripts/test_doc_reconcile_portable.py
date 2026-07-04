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
