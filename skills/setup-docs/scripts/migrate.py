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


def apply_moves(root, move_plan):
    """root 트리에서 move_plan대로 파일 이동 + 트리 내 전 .md 링크 재작성.
    dest가 이동 대상 아닌 기존 파일과 충돌하면 ValueError(사전 STOP, 조용한 덮어쓰기 차단).
    쓰기는 2단계(모든 목적지 기록 → 이동으로 비워진 옛 경로만 삭제)로 chained-move
    (dest==다른 src) 내용 소실을 막는다."""
    root = Path(root)
    move_map = {p["src"]: p["dest"] for p in move_plan}
    srcs = set(move_map)
    # 사전 충돌 감지: dest가 이미 있고, 그게 이동으로 비워질 src가 아니면 STOP.
    clash = sorted(p["dest"] for p in move_plan
                   if (root / p["dest"]).exists() and p["dest"] not in srcs)
    if clash:
        raise ValueError(f"기존 파일과 목적지 충돌(덮어쓰기 위험): {clash}")
    # 1) 모든 .md의 이동전 경로 → 재작성 내용 계산(이동 전 전량 메모리 확보).
    rewritten = {}
    for md in root.rglob("*.md"):
        old_rel = md.relative_to(root).as_posix()
        rewritten[old_rel] = rewrite_links(
            md.read_text(encoding="utf-8", errors="surrogateescape"), old_rel, move_map)
    dests = {move_map.get(old_rel, old_rel) for old_rel in rewritten}
    # 2) 모든 목적지에 먼저 기록(내용은 메모리에 있어 dest==다른 src여도 안전).
    for old_rel, new_text in rewritten.items():
        dst = root / move_map.get(old_rel, old_rel)
        dst.parent.mkdir(parents=True, exist_ok=True)
        # surrogateescape로 읽은 invalid UTF-8 바이트를 그대로 되쓴다(소실 0, G2).
        dst.write_text(new_text, encoding="utf-8", errors="surrogateescape")
    # 3) 이동으로 비워진 옛 경로만 삭제(누군가의 목적지인 경로는 보존).
    for old_rel in rewritten:
        new_rel = move_map.get(old_rel, old_rel)
        if new_rel != old_rel and old_rel not in dests:
            (root / old_rel).unlink()


def _ensure_folder_index(folder):
    """폴더의 인덱스(gate.index_of 규칙: _README.md > README.md). 없으면 _README.md 생성."""
    folder = Path(folder)
    idx = gate.index_of(folder)
    if idx:
        return idx
    folder.mkdir(parents=True, exist_ok=True)
    idx = folder / "_README.md"
    idx.write_text(f"# {folder.name}\n", encoding="utf-8")
    return idx


def _home_links_index(home_text, rel):
    """home이 rel 폴더의 인덱스에 도달하는 링크(dir 링크 또는 _README/README 파일 링크)를
    이미 가졌는지. 하위 임의 파일 링크(예: rel/other.md)는 인덱스 도달을 보장 못 하므로 제외 —
    느슨한 substring 매칭이 새 중첩 폴더를 '이미 링크됨'으로 오탐해 orphan을 남기던 버그(F1) 방지."""
    return (f"]({rel}/)" in home_text
            or f"]({rel}/_README.md)" in home_text
            or f"]({rel}/README.md)" in home_text)


def _append_links(path, entries):
    """entries=[(label, target)] → '- [label](target)' 를 path에 append(멱등: 이미 있으면 skip).
    기존 내용과 빈 줄로 분리해 기존 마지막 세그먼트에 붙지 않게 한다(content_oracle 오탐/false STOP 방지)."""
    text = path.read_text(encoding="utf-8")
    add = [f"- [{lab}]({t})" for lab, t in entries if f"]({t})" not in text]
    if not add:
        return
    block = "\n".join(add) + "\n"
    if not text:
        path.write_text(block, encoding="utf-8")
        return
    if text.endswith("\n\n"):
        sep = ""
    elif text.endswith("\n"):
        sep = "\n"
    else:
        sep = "\n\n"
    path.write_text(text + sep + block, encoding="utf-8")


def _index_home(root):
    """INDEX_MARKER를 담은 파일(docs/_map.md 우선, 없으면 진입 라우터). 없으면 None."""
    root = Path(root)
    for c in [root / "docs" / "_map.md"] + [root / n for n in ENTRY_FILENAMES]:
        if c.is_file() and INDEX_MARKER in c.read_text(encoding="utf-8", errors="ignore"):
            return c
    return None


def register_in_indexes(root, move_plan):
    """이동 문서를 도달 가능하게 배선(orphan=0). scaffold spine 위에 얹는다.

    폴더 문서 → 폴더 인덱스에 링크(+아직 map에 안 걸린 폴더만 map에 등록) · 평면 문서 → index home에 직접.
    링크 타겟은 home 위치 기준 상대. 멱등."""
    root = Path(root)
    home = _index_home(root)
    home_dir = home.parent.relative_to(root).as_posix() if home else ""
    home_text = home.read_text(encoding="utf-8") if home else ""

    by_folder, flats = {}, []
    for p in move_plan:
        dest = p["dest"]
        folder = posixpath.dirname(dest)
        if folder == "docs":
            flats.append(dest)
        else:
            by_folder.setdefault(folder, []).append(posixpath.basename(dest))

    map_entries = []
    for folder, names in sorted(by_folder.items()):
        idx = _ensure_folder_index(root / folder)
        _append_links(idx, [(posixpath.splitext(n)[0], n) for n in sorted(names)])
        rel = posixpath.relpath(folder, home_dir or ".")   # home 기준 폴더 경로
        if not _home_links_index(home_text, rel):          # 폴더 인덱스에 도달하는 링크가 아직 없을 때만
            map_entries.append((posixpath.basename(folder), rel + "/"))
    for dest in sorted(flats):
        rel = posixpath.relpath(dest, home_dir or ".")
        map_entries.append((posixpath.splitext(posixpath.basename(dest))[0], rel))

    if home and map_entries:
        _append_links(home, map_entries)


_COPY_IGNORE = shutil.ignore_patterns("node_modules", ".git", "dist", "build", "vendor")


def _copy_tree(repo, dst):
    """repo → dst 복사(제외 디렉터리 빼고). base·current가 동일 파일집합을 보게 해 content_oracle 오탐 방지."""
    shutil.copytree(repo, dst, ignore=_COPY_IGNORE, dirs_exist_ok=True)


def build_and_verify(repo, move_plan, plugin_root=None):
    """두 스크래치(base=원본 복사, current=복사+이동+scaffold+등록)로 검증 →
    {broken, orphan, unaccounted}. 실제 repo는 안 건드림."""
    repo = Path(repo).resolve()
    base = Path(tempfile.mkdtemp(prefix="docsherpa-base-"))
    current = Path(tempfile.mkdtemp(prefix="docsherpa-cur-"))
    try:
        _copy_tree(repo, base)
        _copy_tree(repo, current)
        apply_moves(current, move_plan)
        scaffold.scaffold(current, plugin_root_dir=plugin_root)
        register_in_indexes(current, move_plan)
        res = gate.analyze(current)
        base_keys = set(content_oracle.collect(base))
        cur_keys = set(content_oracle.collect(current))
        unaccounted = sorted(base_keys - cur_keys)
        return {"broken": len(res.broken), "orphan": len(res.orphans),
                "unaccounted": unaccounted}
    finally:
        shutil.rmtree(base, ignore_errors=True)
        shutil.rmtree(current, ignore_errors=True)


def _after_tree(move_plan):
    """move_plan → "후" 트리 dict (tag='목표', 문서들을 'new'로 표시)."""
    lines = [["docs/", None]]
    for p in move_plan[:12]:
        lines.append([p["dest"], "new"])
    sub = f"docs/ 중앙집중 · 이동 {len(move_plan)}건"
    return {"title": "docs/ 중앙집중", "tag": "목표", "sub": sub, "lines": lines}


def assemble_plan_data(health, move_plan, decisions=None):
    """doc-health 부분 dict → render_report plan 계약(trees.after·migration·decisions 추가)."""
    data = dict(health)
    data["trees"] = dict(data.get("trees", {}))
    data["trees"]["after"] = _after_tree(move_plan)
    data["migration"] = list(move_plan)
    data["decisions"] = list(decisions or [])
    data.setdefault("summary", {})
    return data
