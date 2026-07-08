#!/usr/bin/env python3
"""문서 건강 점수표 — doc-health 채점(기계 차원 M1~M5 + 등급 rollup).

도달성은 gate.analyze 재사용(단일 엔진 = 정합성). disposition(H1)으로 M5 분모 결정.
J1~J4 판단·분류·자세 하위는 SKILL.md 절차(코드 아님).
"""
import json
import sys
from pathlib import Path

# --- 공유 스크립트 경로 부트스트랩(CLI 실행 시; 테스트는 conftest.py도) ---------
_SHARED = Path(__file__).resolve().parents[2] / "setup-docs" / "scripts"
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))

import contract  # noqa: E402
import gate       # noqa: E402

# --- 임계값 (🔴 열린질문 — 하드닝 루프 튜닝, spec §3c) -------------------------
M5_WARN_MAX = 3       # docs/ 밖 content 1~3 = warn, 초과 = fail
ORPHAN_MOST = 0.5     # orphan_ratio >= 이 값이면 "대부분 미도달"(F)
J_WARN_MAX = 2        # J warn 1~2 = B 유지, 초과 = C
GREENFIELD_MAX = 2    # content 문서 이하 + 라우터 없음 = GREENFIELD

# --- disposition (H1) --------------------------------------------------------
_TOOLING_DIRS = (".claude", ".github", ".cursor", ".gitlab")
_ROOT_CONVENTION = {"README.md", "CONTRIBUTING.md", "CHANGELOG.md",
                    "SECURITY.md", "CODE_OF_CONDUCT.md"}


def disposition(rel_path):
    """repo-상대 경로 → 'router'|'tooling'|'content' (경로 규칙, 판단 아님)."""
    parts = Path(rel_path).parts
    name = parts[-1]
    if len(parts) == 1 and name in contract.ENTRY_FILENAMES:
        return "router"
    if parts and parts[0] in _TOOLING_DIRS:
        return "tooling"
    if len(parts) == 1 and name in _ROOT_CONVENTION:
        return "tooling"
    return "content"


def outside_content(files):
    """docs/ 밖 content 문서 목록(M5 위반 후보) — 정렬."""
    out = [f for f in files
           if disposition(f) == "content" and Path(f).parts[0] != "docs"]
    return sorted(out)


# --- 기계 차원 M1~M5 ---------------------------------------------------------
def _has_sessionstart_hook(settings_path):
    if not settings_path.is_file():
        return False
    try:
        return "SessionStart" in settings_path.read_text(encoding="utf-8")
    except OSError:
        return False


def _m4_loop_ok(root):
    root = Path(root)
    return ((root / ".claude" / "doc-drift-prime.txt").is_file()
            and (root / ".claude" / "skills" / "doc-reconcile" / "SKILL.md").is_file()
            and _has_sessionstart_hook(root / ".claude" / "settings.json"))


def _m5_status(files):
    n = len(outside_content(files))
    if n == 0:
        return "pass"
    return "warn" if n <= M5_WARN_MAX else "fail"


def machine_dims(res, files):
    """GateResult + inventory files → [M1..M5] 차원 dict 리스트."""
    root = res.root
    n_home = len(res.homes)
    m1 = "pass" if (not res.broken and not res.orphans) else "fail"
    m2 = "pass" if (res.router_present and n_home == 1) else "fail"
    map_home = (root / "docs" / "_map.md").resolve()
    m3 = "pass" if (n_home == 1 and res.homes[0].resolve() == map_home) else "fail"
    m4 = "pass" if _m4_loop_ok(root) else "fail"
    m5 = _m5_status(files)
    outside = outside_content(files)
    return [
        {"code": "M1", "name": "도달성", "status": m1,
         "sub": f"broken={len(res.broken)} · orphan={len(res.orphans)}"},
        {"code": "M2", "name": "라우터+마커", "status": m2,
         "sub": ("라우터 없음" if not res.router_present
                 else f"마커 home {n_home}개"
                 + ("" if n_home == 1 else " (정확히 1 필요)"))},
        {"code": "M3", "name": "맵 척추", "status": m3,
         "sub": ("home=docs/_map.md" if m3 == "pass"
                 else "척추 미분리(인라인 마커 또는 home≠1)")},
        {"code": "M4", "name": "성장 루프", "status": m4,
         "sub": ("prime·hook·doc-reconcile 설치" if m4 == "pass"
                 else "성장 루프 3종 중 누락")},
        {"code": "M5", "name": "커버리지", "status": m5,
         "sub": (f"docs/ 밖 content {len(outside)}건" if outside
                 else "docs/ 밖 content 0")},
    ]


# --- 등급 rollup (결정론, 임계값 🔴 튜닝) --------------------------------------
def rollup(mech, judg, orphan_ratio, router_present):
    """9차원 상태 + 신호 → 등급 'A'..'F' (spec §3c 산식)."""
    m = {d["code"]: d["status"] for d in mech}
    if not router_present:
        return "F"
    if m["M1"] == "fail" and orphan_ratio >= ORPHAN_MOST:
        return "F"
    if m["M1"] == "fail":
        return "D"
    if m["M5"] == "fail":
        return "D"
    # 여기서 M1 == pass
    m_nonpass = sum(1 for c in ("M2", "M3", "M4", "M5") if m[c] != "pass")
    if m_nonpass >= 3:
        return "D"
    if m_nonpass >= 1:
        return "C"
    # M1~M5 전부 pass
    js = [d["status"] for d in judg]
    j_fail = sum(1 for s in js if s == "fail")
    j_warn = sum(1 for s in js if s == "warn")
    if j_fail or j_warn > J_WARN_MAX:
        return "C"
    if 1 <= j_warn <= J_WARN_MAX:
        return "B"
    return "A"


def counts(mech, judg):
    """전 9차원 상태 tally → {fail,warn,pass}."""
    alld = list(mech) + list(judg)
    return {k: sum(1 for d in alld if d["status"] == k)
            for k in ("fail", "warn", "pass")}


def posture_hint(res, files, mech):
    """결정론 자세 힌트. MESSY 하위 구분은 에이전트 판단(SKILL)."""
    m = {d["code"]: d["status"] for d in mech}
    content = [f for f in files if disposition(f) == "content"]
    if not res.router_present and len(content) <= GREENFIELD_MAX:
        return "GREENFIELD"
    if res.router_present and m["M1"] == "pass" and m["M5"] == "pass":
        return "HEALTHY"
    return "MESSY"


# --- 조립 + CLI --------------------------------------------------------------
def _git_branch(root):
    head = Path(root) / ".git" / "HEAD"
    try:
        txt = head.read_text(encoding="utf-8").strip()
    except OSError:
        return "?"
    prefix = "ref: refs/heads/"
    return txt[len(prefix):] if txt.startswith(prefix) else txt[:8]


def _before_tree(files):
    outside = outside_content(files)
    lines = []
    if any(Path(f).parts[0] == "docs" for f in files):
        lines.append(["docs/", None])
    for f in outside[:12]:
        lines.append([f, "stray"])
    sub = (f"docs/ 밖 흩어짐 · content {len(outside)}건" if outside
           else "docs/ 중심")
    return {"title": "현재 구조", "tag": "지금", "sub": sub, "lines": lines}


def assemble(root, files, judgment, inventory=None):
    """root + inventory files + 에이전트 판단 J차원 → render_report 부분 데이터 모델."""
    res = gate.analyze(root)
    mech = machine_dims(res, files)
    orphan_ratio = (len(res.orphans) / len(res.all_docs)) if res.all_docs else 0.0
    grade = rollup(mech, judgment, orphan_ratio, res.router_present)
    out = {
        "repo": {"name": Path(root).resolve().name,
                 "docs_count": len(files),
                 "branch": _git_branch(root)},
        "grade": {"current": grade, "target": "A"},
        "counts": counts(mech, judgment),
        "scorecard": {"mechanical": mech, "judgment": judgment},
        "trees": {"before": _before_tree(files)},
        "posture": posture_hint(res, files, mech),
    }
    if inventory is not None:
        out["inventory"] = inventory
    return out


def main(argv=None):
    import argparse
    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--manifest", help="분류 매니페스트 JSON([{path,type,...}])")
    ap.add_argument("--judgment", required=True,
                     help="J1~J4 판단 차원 JSON([{code,name,sub,status}]) — "
                          "9차원(M1~M5+J1~J4) 전부 평가해야 정직한 등급이므로 필수")
    args = ap.parse_args(argv)

    import inventory as _inv
    files = _inv.list_docs(args.root)
    manifest = None
    if args.manifest:
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    judgment = json.loads(Path(args.judgment).read_text(encoding="utf-8"))
    data = assemble(args.root, files, judgment, inventory=manifest)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
