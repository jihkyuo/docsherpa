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
import subprocess
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
    missing = [p["src"] for p in move_plan if not (root / p["src"]).exists()]
    if missing:
        raise ValueError(f"move_plan.src 부재(조용한 no-op 차단): {missing}")
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
        if not md.is_file():
            continue
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


def prune_empty_dirs(root):
    """이동으로 빈 디렉터리를 제거(R4: git 빈폴더 미커밋 → dir 링크 커밋후 파손 방지). 루트는 보존.
    deepest-first로 삭제 시점에 빈 여부를 재검사 → 자식을 먼저 지우면 부모가 그 시점에 비어 연쇄 제거되므로
    중첩 빈 폴더까지 정리된다. 권한거부·경합 삭제는 try/except로 방어(그 폴더만 skip)."""
    root = Path(root)
    for d in sorted((p for p in root.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
        try:
            if d != root and not any(d.iterdir()):
                d.rmdir()
        except OSError:
            pass


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
    느슨한 substring 매칭이 새 중첩 폴더를 '이미 링크됨'으로 오탐해 orphan을 남기던 버그(F1) 방지.
    펜스 코드블록(예시 문법)은 제거 후 검사 — 펜스 속 예시가 실링크로 오탐되는 것 방지(R5)."""
    home_text = gate.FENCE_RE.sub("", home_text)
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


def _live_link_targets(text):
    """gate와 동일 의미론: 펜스 코드블록 제거 후 실제 ](target) 만 추출(raw substring 오탐 방지, R5)."""
    return set(gate.LINK_RE.findall(gate.FENCE_RE.sub("", text)))


def _append_links_live(path, entries):
    """_append_links와 동일하나 '이미 있음' 판정을 live-link 파싱으로(R5). 반환=신규 추가 수."""
    text = path.read_text(encoding="utf-8", errors="surrogateescape") if path.exists() else ""
    have = _live_link_targets(text)
    add = [(lab, t) for lab, t in entries if t not in have]
    if not add:
        return 0
    block = "\n".join(f"- [{lab}]({t})" for lab, t in add) + "\n"
    sep = "" if text.endswith("\n\n") else ("\n" if text.endswith("\n") else ("\n\n" if text else ""))
    path.write_text(text + sep + block, encoding="utf-8", errors="surrogateescape")
    return len(add)


def register_all(root):
    """도달성-구동: gate가 orphan으로 보는 docs/**/*.md 전부를 폴더 인덱스·map에 배선.
    이동/제자리/legacy 균일(L3). 진행 가드로 미수렴 시 RuntimeError(R5).
    root은 resolve() — gate.analyze가 내부에서 root를 resolve하므로(예: macOS /tmp→/private/tmp
    심링크) 안 맞추면 orphans의 relative_to(root)가 ValueError로 터진다(build_and_verify가
    tempfile.mkdtemp()의 미resolve 경로를 넘길 때 실제로 발생)."""
    root = Path(root).resolve()
    while True:
        orphans = [p.relative_to(root).as_posix() for p in gate.analyze(root).orphans]
        if not orphans:
            return
        added = _register_orphan_rels(root, orphans)
        if added == 0:
            raise RuntimeError(f"register_all 미수렴 — 등록 불가 orphan: {orphans}")


def _register_orphan_rels(root, rels):
    """orphan 상대경로들을 폴더별로 묶어 인덱스+map에 등록. 반환=신규 링크 수(진행 측정)."""
    home = _index_home(root)
    if home is None:
        raise RuntimeError("register_all 미수렴 — index home(맵/라우터 마커) 없음")
    home_dir = home.parent.relative_to(root).as_posix()
    home_text = home.read_text(encoding="utf-8", errors="surrogateescape")
    by_folder, flats, added = {}, [], 0
    for rel in rels:
        folder = posixpath.dirname(rel)
        (flats if folder == "docs" else by_folder.setdefault(folder, [])).append(rel)
    map_entries = []
    for folder, items in sorted(by_folder.items()):
        idx = _ensure_folder_index(root / folder)
        names = sorted(posixpath.basename(r) for r in items if (root / folder / posixpath.basename(r)) != idx)
        added += _append_links_live(idx, [(posixpath.splitext(n)[0], n) for n in names])
        rel_to_home = posixpath.relpath(folder, home_dir or ".")
        if not _home_links_index(home_text, rel_to_home):
            map_entries.append((posixpath.basename(folder), rel_to_home + "/"))
    for rel in sorted(flats):
        map_entries.append((posixpath.splitext(posixpath.basename(rel))[0], posixpath.relpath(rel, home_dir or ".")))
    if map_entries:
        added += _append_links_live(home, map_entries)
    return added


_COPY_IGNORE = shutil.ignore_patterns("node_modules", ".git", "dist", "build", "vendor")


def _copy_tree(repo, dst):
    """repo → dst 복사(제외 디렉터리 빼고). base·current가 동일 파일집합을 보게 해 content_oracle 오탐 방지."""
    shutil.copytree(repo, dst, ignore=_COPY_IGNORE, dirs_exist_ok=True)


def verify_migration(base_root, cur_root, move_plan):
    """세 오라클 + per-file + 미설명 broken 안전망 일원화(Phase 1b·Phase 3 공유). 반환 dict.

    unexplained_broken: gate가 cur 전체에서 본 broken 링크 중 classify_links의
    new_broken∪preexisting_broken으로 설명되지 않는 것. classify_links는 base 문서만 페어링하므로
    cur-only 파일(scaffold의 _map/router·register_all의 폴더 인덱스)의 broken 파일-링크는 거기 안
    잡히고 orphan(미도달)도 아니라 랜딩 게이트를 새어나갈 수 있다(증분3이 gate.analyze.broken 전체를
    직접 게이트하던 안전망을 T6 재배선이 떨어뜨림). register_all 후 orphan=0이라 gate가 cur 전
    문서를 방문하므로 gate.broken이 cur 전체 broken을 커버한다."""
    base_keys = set(content_oracle.collect(base_root))
    cur_keys = set(content_oracle.collect(cur_root))
    links = classify_links(base_root, cur_root, move_plan)
    gres = gate.analyze(cur_root)
    cur_r = Path(cur_root).resolve()
    explained = set(links["new_broken"]) | set(links["preexisting_broken"])
    unexplained_broken = sorted(
        (src.relative_to(cur_r).as_posix(), raw) for src, raw in gres.broken
        if (src.relative_to(cur_r).as_posix(), raw) not in explained)
    return {
        "unaccounted": sorted(base_keys - cur_keys),
        "new_broken": links["new_broken"],
        "preexisting_broken": links["preexisting_broken"],
        "anchor_lost": links["anchor_lost"],
        "orphan": len(gres.orphans),
        "unexplained_broken": unexplained_broken,
        "per_file": per_file_accounting(base_root, cur_root, move_plan),
    }


def build_and_verify(repo, move_plan, plugin_root=None):
    """두 스크래치(base=원본 복사, current=복사+이동+scaffold+등록)로 검증 →
    {broken, orphan, unaccounted, new_broken, anchor_lost, per_file}. 실제 repo는 안 건드림."""
    repo = Path(repo).resolve()
    base = Path(tempfile.mkdtemp(prefix="docsherpa-base-"))
    current = Path(tempfile.mkdtemp(prefix="docsherpa-cur-"))
    try:
        _copy_tree(repo, base)
        _copy_tree(repo, current)
        apply_moves(current, move_plan)
        prune_empty_dirs(current)
        scaffold.scaffold(current, plugin_root_dir=plugin_root)
        register_all(current)
        v = verify_migration(base, current, move_plan)
        return {"broken": len(v["new_broken"]), "orphan": v["orphan"],
                "unaccounted": v["unaccounted"], "new_broken": v["new_broken"],
                "anchor_lost": v["anchor_lost"], "unexplained_broken": v["unexplained_broken"],
                "per_file": v["per_file"]}
    finally:
        shutil.rmtree(base, ignore_errors=True)
        shutil.rmtree(current, ignore_errors=True)


def _git_out(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=True).stdout


def land_migration(repo, move_plan, head_sha, decisions=None, *, plugin_root=None):
    """검증된 계획을 worktree 격리로 실 브랜치에 랜딩(R3·R8). 통과 시에만 커밋, 실패/크래시 흔적0.

    이중 worktree(wt_cur=적용 대상 새 브랜치, wt_base=오라클 base 둘 다 head_sha에서 분기) →
    apply_moves→prune_empty_dirs→scaffold→register_all(wt_cur) → verify_migration(wt_base, wt_cur).
    검증한 그 wt_cur를 그대로 커밋(재실행 없음). finally에서 worktree 2개 제거, 이번 호출이 만든
    브랜치를 커밋 못 했을 때만 삭제(재호출로 남의 성공 브랜치 force-delete 방지)."""
    repo = Path(repo).resolve()
    if not (repo / ".git").exists():
        raise RuntimeError("git repo 아님 — land_migration은 git 전제(git init 선행).")
    cur_head = _git_out(repo, "rev-parse", "HEAD").strip()
    if cur_head != head_sha:
        raise RuntimeError(f"HEAD 스테일(계획 시 {head_sha[:8]} ≠ 현재 {cur_head[:8]}) — 재진단 필요.")
    stamp = head_sha[:8]
    branch = f"docsherpa/migrate-{stamp}"
    # 브랜치명은 head_sha 결정론 → 이미 이 커밋의 랜딩 브랜치가 있으면 조용히 덮지 말고 STOP.
    # (자동머지 안 하므로 성공 후 HEAD 불변 → 재호출이 일상 경로. 남의 성공 브랜치 보호 = 내용 소실 0.)
    if subprocess.run(["git", "-C", str(repo), "branch", "--list", branch],
                      capture_output=True, text=True).stdout.strip():
        raise RuntimeError(f"이미 이 커밋에 대한 랜딩 브랜치 {branch}가 있음 — 검토·머지 후 재실행하거나 삭제하라.")
    wt_cur = Path(tempfile.mkdtemp(prefix="docsherpa-land-"))
    wt_base = Path(tempfile.mkdtemp(prefix="docsherpa-base-"))
    branch_created = False
    committed = False
    try:
        subprocess.run(["git", "-C", str(repo), "worktree", "add", "-q", "-b", branch, str(wt_cur), head_sha], check=True)
        branch_created = True                                       # 이번 호출이 만든 브랜치(뒤 단계 실패 시에만 삭제 대상)
        subprocess.run(["git", "-C", str(repo), "worktree", "add", "-q", "--detach", str(wt_base), head_sha], check=True)
        apply_moves(wt_cur, move_plan)
        prune_empty_dirs(wt_cur)
        scaffold.scaffold(wt_cur, plugin_root_dir=plugin_root)
        register_all(wt_cur)
        v = verify_migration(wt_base, wt_cur, move_plan)
        ok = (not v["unaccounted"] and not v["new_broken"] and not v["anchor_lost"]
              and v["orphan"] == 0 and not v["unexplained_broken"] and not v["per_file"])
        if not ok:
            raise RuntimeError(f"랜딩 오라클 실패 → 흔적0 STOP: { {k: v[k] for k in ('unaccounted', 'new_broken', 'anchor_lost', 'orphan', 'unexplained_broken', 'per_file')} }")
        subprocess.run(["git", "-C", str(wt_cur), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(wt_cur), "commit", "-q", "-m",
                        f"📦 docs: docsherpa 마이그레이션(이동 {len(move_plan)}건, 검증트리=커밋트리)"], check=True)
        committed = True
        return {"branch": branch, "unaccounted": [], "new_broken": [], "anchor_lost": [],
                "preexisting_broken": v["preexisting_broken"], "moved": len(move_plan)}
    finally:
        subprocess.run(["git", "-C", str(repo), "worktree", "remove", "--force", str(wt_cur)],
                        capture_output=True)
        subprocess.run(["git", "-C", str(repo), "worktree", "remove", "--force", str(wt_base)],
                        capture_output=True)
        shutil.rmtree(wt_cur, ignore_errors=True); shutil.rmtree(wt_base, ignore_errors=True)
        subprocess.run(["git", "-C", str(repo), "worktree", "prune"], capture_output=True)  # remove 실패 시 메타 잔존 폴백
        if branch_created and not committed:
            subprocess.run(["git", "-C", str(repo), "branch", "-D", branch], capture_output=True)  # 이번 호출이 만든 미커밋 브랜치만 삭제(흔적0, R8)


def _after_tree(move_plan):
    """move_plan → "후" 트리 dict (tag='목표', 문서들을 'new'로 표시)."""
    lines = [["docs/", None]]
    for p in move_plan[:12]:
        lines.append([p["dest"], "new"])
    sub = f"docs/ 중앙집중 · 이동 {len(move_plan)}건"
    return {"title": "docs/ 중앙집중", "tag": "목표", "sub": sub, "lines": lines}


def doc_links(root, rel):
    """도달성 무관, 한 문서의 본문 링크들을 해석. resolve는 gate.resolve(파일위치 기준).

    본문 링크(](target))만 본다 — 라우터 import(@AGENTS.md)는 제외한다. gate.targets_in은
    import 매치를 링크 매치보다 앞에 반환하는데, scaffold의 inject_claude_md가 import를 CLAUDE.md
    맨 앞에 prepend하면 그 앞선 import 한 줄이 링크 리스트 인덱스를 통째로 밀어 classify_links의
    zip-by-index 정렬을 깨뜨린다(무손실 마이그레이션이 오분류 → 거짓 STOP/거짓 PASS). import는
    라우터 메커니즘이고 도달성은 gate가 별도로 본다."""
    root = Path(root); path = root / rel
    text = path.read_text(encoding="utf-8", errors="surrogateescape")   # G2 일관
    out = []
    for raw in gate.LINK_RE.findall(gate.FENCE_RE.sub("", text)):       # 펜스 제거 후 본문 링크만
        kind, target = gate.resolve(path, raw)
        anchor = raw.split("#", 1)[1] if "#" in raw else ""
        if kind == "skip":
            out.append({"raw": raw, "kind": "skip", "resolved": True, "anchor": anchor}); continue
        if kind == "dir":
            resolved = Path(target).is_dir()
        else:  # file
            resolved = (not target.name.endswith(".md")) or target.is_file()   # 비-.md는 gate가 skip(해석성공 취급)
        out.append({"raw": raw, "kind": kind, "resolved": resolved, "anchor": anchor})
    return out


def classify_links(base_root, cur_root, move_plan):
    """소스정체성 페어링(R1): base 문서 ↔ cur 문서(move_map) · 링크 index zip.
    new_broken = base-satisfiable & cur-broken. preexisting = 둘 다 broken. anchor_lost = 앵커 축소.

    zip-by-index 가정: register_in_indexes/register_all은 새 링크를 인덱스 문서 "끝에" append하므로
    (append-at-end), cur의 링크 리스트는 base와 같은 순서로 시작해 뒤에 신규 항목만 덧붙는다.
    그래서 base[i]↔cur[i]로 앞에서부터 zip해도 정렬이 어긋나지 않는다.

    cur 링크 감소 시 차단 방향 폴백(정체성 fail-safe): cur가 링크를 잃으면(len(cl)<len(bl):
    삭제/재정렬) index 페어링이 붕괴해 자가유발 broken을 preexisting로 은폐할 수 있다. 그 문서는
    zip을 신뢰하지 않고 cur의 broken 링크를 전부 new_broken(차단)으로 분류한다."""
    base_root, cur_root = Path(base_root), Path(cur_root)
    move_map = {p["src"]: p["dest"] for p in move_plan}
    res = {"new_broken": [], "preexisting_broken": [], "anchor_lost": []}
    for bmd in sorted(base_root.rglob("*.md")):
        if not bmd.is_file():
            continue
        old_rel = bmd.relative_to(base_root).as_posix()
        new_rel = move_map.get(old_rel, old_rel)
        if not (cur_root / new_rel).is_file():
            continue                                   # dest 부재는 per_file 회계(Task 4)가 담당
        bl = [l for l in doc_links(base_root, old_rel) if l["kind"] != "skip"]
        cl = [l for l in doc_links(cur_root, new_rel) if l["kind"] != "skip"]
        if len(cl) < len(bl):                          # 링크 감소 → 정렬 붕괴, 차단 방향 폴백
            for c in cl:
                if not c["resolved"]:
                    res["new_broken"].append((new_rel, c["raw"]))
            continue
        for i, b in enumerate(bl):                     # append-at-end(register)라 base index가 앞에서 정렬
            c = cl[i] if i < len(cl) else None
            if c is None:
                continue
            if b["resolved"] and not c["resolved"]:
                res["new_broken"].append((new_rel, c["raw"]))
            elif not b["resolved"] and not c["resolved"]:
                res["preexisting_broken"].append((new_rel, c["raw"]))
            if b["anchor"] and b["anchor"] != c["anchor"]:
                res["anchor_lost"].append((new_rel, c["raw"]))
    return res


def per_file_accounting(base_root, cur_root, move_plan):
    """각 base 문서의 세그먼트 집합이 그 dest 파일에 존재하는지(파일 단위 회계, R7).
    content_oracle의 '고유 세그먼트 집합' 사각(같은 내용 여러 문서 중 일부 소실)을 base 문서마다
    dest 도달을 확인해 보완한다. dest 부재 또는 세그먼트 미도달을 잡는다. 반환=위반 리스트([]=ok)."""
    base_root, cur_root = Path(base_root), Path(cur_root)
    move_map = {p["src"]: p["dest"] for p in move_plan}
    viol = []
    for bmd in sorted(base_root.rglob("*.md")):
        if not bmd.is_file():
            continue
        old_rel = bmd.relative_to(base_root).as_posix()
        new_rel = move_map.get(old_rel, old_rel)
        dest = cur_root / new_rel
        if not dest.is_file():
            viol.append((new_rel, "dest 파일 미도달")); continue
        base_keys = {content_oracle.seg_key(s)
                     for s in content_oracle.segment(bmd.read_text(encoding="utf-8", errors="surrogateescape"))}
        dest_keys = {content_oracle.seg_key(s)
                     for s in content_oracle.segment(dest.read_text(encoding="utf-8", errors="surrogateescape"))}
        missing = base_keys - dest_keys
        if missing:
            viol.append((new_rel, f"세그먼트 dest 미도달 {len(missing)}건"))
    return viol


def assemble_plan_data(health, move_plan, decisions=None):
    """doc-health 부분 dict → render_report plan 계약(trees.after·migration·decisions 추가)."""
    data = dict(health)
    data["trees"] = dict(data.get("trees", {}))
    data["trees"]["after"] = _after_tree(move_plan)
    data["migration"] = list(move_plan)
    data["decisions"] = list(decisions or [])
    data.setdefault("summary", {})
    return data
