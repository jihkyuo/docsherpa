"""언어-불문 섹션 계약 검증 — doc-reconcile이 의존하는 마커가 있는지.

spec D8: 헤딩 문자열이 아니라 HTML 마커를 계약으로 삼는다.
마커 상수의 정본은 contract.py — 여기선 하위호환 재-export.
"""
from contract import ROUTING_MARKER, INDEX_MARKER


def has_contract_markers(agents_md_text: str) -> bool:
    return ROUTING_MARKER in agents_md_text and INDEX_MARKER in agents_md_text
