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


_URL_RE = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")   # [label](target)
_EXTERNAL = ("http://", "https://", "mailto:", "tel:", "#", "/")   # "/" = 루트상대(F6)


def _relpath(from_file, to_file):
    """repo-상대 POSIX 두 경로 → from_file 위치 기준 to_file 상대경로."""
    return posixpath.relpath(to_file, posixpath.dirname(from_file) or ".")


def rewrite_links(text, old_self, move_map):
    """text의 마크다운 링크를, 문서가 old_self→move_map[old_self]로 이동한다는 전제로 재작성.
    이동한 타겟은 새 경로로, 안 움직인 타겟도 새 자기위치 기준 상대경로로.
    후행 슬래시(디렉터리 링크) 보존 · 외부/앵커/루트상대 skip(F6)."""
    new_self = move_map.get(old_self, old_self)
    old_dir = posixpath.dirname(old_self)

    def repl(m):
        label, raw = m.group(1), m.group(2).strip()
        if not raw or raw.startswith(_EXTERNAL):
            return m.group(0)
        target, hashsep, anchor = raw.partition("#")
        if not target:
            return m.group(0)
        trailing = "/" if target.endswith("/") else ""
        old_target = posixpath.normpath(posixpath.join(old_dir, target))
        new_target = move_map.get(old_target, old_target)
        newrel = _relpath(new_self, new_target) + trailing
        return f"[{label}]({newrel}{hashsep}{anchor})"

    return _URL_RE.sub(repl, text)
