"""언어-불문 섹션 계약 검증 — doc-reconcile이 의존하는 마커가 AGENTS.md에 있는지.

spec D8: 헤딩 문자열(번역·wording에 취약)이 아니라 HTML 마커를 계약으로 삼는다.
"""

ROUTING_MARKER = "<!-- docsherpa:routing -->"
INDEX_MARKER = "<!-- docsherpa:index -->"


def has_contract_markers(agents_md_text: str) -> bool:
    return ROUTING_MARKER in agents_md_text and INDEX_MARKER in agents_md_text
