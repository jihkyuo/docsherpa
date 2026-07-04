"""§7.5 앵커 특화용 신호 탐지 — target repo에 어떤 정본 문서-타입이 실재하는지.

doc-reconcile의 "자주 새는 앵커"를 그 프로젝트에 맞게 특화할 때, **확신되는 것만**
특화하고 없으면 일반형을 유지한다(hollow 방지, spec §7.5). 이 함수는 그 "확신"의
근거 — 실재하는 문서-타입만 경로로 보고하고, 없으면 None.
"""
from pathlib import Path

# 앵커 테마 → 후보 경로(우선순위 순). 첫 실재하는 것을 채택.
_SPEC = ["docs/DESIGN.md", "docs/SPEC.md", "docs/design.md", "docs/spec.md"]
_CODEMAP = ["docs/ARCHITECTURE.md", "docs/architecture.md", "docs/CODEMAP.md", "docs/codemap.md"]
_DECISIONS = ["docs/decisions"]     # 디렉터리
_HOWTO = ["docs/how-to", "docs/how_to"]  # 디렉터리


def _first_file(root: Path, cands):
    for rel in cands:
        if (root / rel).is_file():
            return rel
    return None


def _first_dir(root: Path, cands):
    for rel in cands:
        if (root / rel).is_dir():
            return rel
    return None


def anchor_signals(repo_root) -> dict:
    """{design_spec, decisions, codemap, how_to} — 실재하면 repo-상대 경로, 없으면 None."""
    root = Path(repo_root)
    return {
        "design_spec": _first_file(root, _SPEC),
        "decisions": _first_dir(root, _DECISIONS),
        "codemap": _first_file(root, _CODEMAP),
        "how_to": _first_dir(root, _HOWTO),
    }
