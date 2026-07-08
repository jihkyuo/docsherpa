#!/usr/bin/env python3
"""setup-docs 마이그레이션 엔진 (증분 3 — Phase 1).

결정론: 배정(type→folder) · 링크리라이트 · 물리이동 · 인덱스등록(도달성 배선)
· 스크래치 빌드+검증(두 오라클). 판단(feature명·토픽폴더·동결역사 태깅)은 SKILL 산문.
content_oracle이 링크를 정규화해 무시하므로 내용보존=content_oracle,
링크정확성·도달성=gate(broken=0·orphan=0)가 각각 담당. 의존은 전부 setup-docs/scripts 내부.
"""
import posixpath
import re
import shutil
import tempfile
from pathlib import Path

import content_oracle
import contract
import gate
import scaffold
from contract import ENTRY_FILENAMES, INDEX_MARKER

_TYPE_DEST = {
    "ADR": "docs/decisions",
    "how-to": "docs/how-to",
    "PRD": "docs/product",
    "reference": "docs",
    "explanation": "docs",
}


def plan_moves(inventory):
    """inventory(doc-health) → move_plan. 결정론(type→folder).

    skip: router/tooling(contract.disposition) · legacy(동결역사) · .mdx(무손실 미증명) · 이미제자리.
    spec은 doc["feature"], 토픽폴더는 doc["topic"](SKILL 판단으로 미리 채움)를 쓴다.
    계획 내 목적지 중복 → ValueError(STOP)."""
    plan = []
    for doc in inventory:
        src = doc["path"]
        if contract.disposition(src) in ("router", "tooling"):
            continue
        if doc.get("type") == "legacy" or src.endswith(".mdx"):
            continue                      # 동결역사·.mdx = 제자리(증분 4)
        name = posixpath.basename(src)
        if doc.get("topic"):
            dest = f"docs/{doc['topic']}/{name}"
        elif doc.get("type") == "spec":
            dest = f"docs/specs/{doc.get('feature') or 'misc'}/{name}"
        else:
            dest = f"{_TYPE_DEST.get(doc.get('type'), 'docs')}/{name}"
        if src == dest:
            continue
        plan.append({"src": src, "dest": dest, "ops": ["move"],
                     "impact": doc.get("impact")})
    dests = [p["dest"] for p in plan]
    dups = sorted({d for d in dests if dests.count(d) > 1})
    if dups:
        raise ValueError(f"목적지 충돌(둘 이상이 같은 경로): {dups}")
    return plan
