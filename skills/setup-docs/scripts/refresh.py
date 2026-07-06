"""doc-reconcile 설치본의 버전 동기(up-only refresh) — 결정론 기계.

플러그인 정본이 새 버전이면 target repo의 설치본을 안전하게 교체한다:
다운그레이드 차단·로컬 편집 보존·이식성. 커밋은 하지 않는다(에이전트가 알림).
상태는 파일 끝 스탬프(<!-- docsherpa-scaffold: v<ver> sha=<12hex> -->)에 담는다.
"""
import hashlib
import json
import re
from pathlib import Path

_STAMP_RE = re.compile(r"\s*<!-- docsherpa-scaffold:.*?-->\s*\Z")
_PARSE_RE = re.compile(r"<!-- docsherpa-scaffold: v(\S+)(?: sha=([0-9a-f]+))? -->")


def strip_stamp(text):
    """파일 끝 스캐폴드 스탬프(있으면)를 제거."""
    return _STAMP_RE.sub("", text)


def canonical_hash(text):
    """스탬프 제거 + 정규화(BOM·CRLF·trailing개행) 후 sha256[:12]. 로컬편집·버전비교 기준."""
    body = strip_stamp(text).lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n").rstrip()
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:12]


def parse_stamp(text):
    """스탬프에서 (version, sha|None). 없으면 None. 파일 끝(마지막) 스탬프를 읽는다
    (본문이 스탬프 예시 문자열을 담아도 진짜 trailing 스탬프를 고른다). 구-스탬프(sha 없음)도 지원."""
    matches = list(_PARSE_RE.finditer(text))
    if not matches:
        return None
    m = matches[-1]
    return (m.group(1), m.group(2))


def make_stamp(version, sha):
    return f"\n<!-- docsherpa-scaffold: v{version} sha={sha} -->\n"


def version_gt(a, b):
    """a > b (점 구분 버전, int-튜플 비교; 비-정수 요소는 0)."""
    def parts(v):
        out = []
        for p in str(v).split("."):
            try:
                out.append(int(p))
            except ValueError:
                out.append(0)
        return tuple(out)
    return parts(a) > parts(b)


def verify_plugin_provenance(plugin_root, target):
    """plugin_root가 target 밖 + plugin.json name==docsherpa 여야 refresh 정당."""
    plug = Path(plugin_root).resolve()
    tgt = Path(target).resolve()
    if plug == tgt or tgt in plug.parents:      # plugin이 target 안 → 부정당
        return False
    pj = plug / ".claude-plugin" / "plugin.json"
    if not pj.is_file():
        return False
    try:
        return json.loads(pj.read_text(encoding="utf-8")).get("name") == "docsherpa"
    except (ValueError, OSError):
        return False


def refresh_loop(repo_root, plugin_root):
    """설치본 doc-reconcile을 플러그인 새 버전으로 안전 갱신. 파일만 쓰고 커밋 안 함.

    반환 dict: action=refreshed|stuck|noop, reason, (from/to 버전).
    - provenance 실패/파일부재/스탬프없음/다운그레이드 → noop
    - 로컬 편집(해시 불일치·sha 없음) → stuck(안 덮음)
    - 상위버전 + 미편집 → 원자적 교체 + 새 스탬프
    """
    root = Path(repo_root)
    plug = Path(plugin_root)
    if not verify_plugin_provenance(plug, root):
        return {"action": "noop", "reason": "provenance"}
    installed = root / ".claude" / "skills" / "doc-reconcile" / "SKILL.md"
    canonical = plug / "skills" / "doc-reconcile" / "SKILL.md"
    pj = plug / ".claude-plugin" / "plugin.json"
    if not (installed.is_file() and canonical.is_file() and pj.is_file()):
        return {"action": "noop", "reason": "missing"}
    text = installed.read_text(encoding="utf-8")
    parsed = parse_stamp(text)
    if parsed is None:
        return {"action": "noop", "reason": "no-stamp"}
    ver_e, sha_e = parsed
    ver_p = json.loads(pj.read_text(encoding="utf-8")).get("version", "0")
    if not version_gt(ver_p, ver_e):
        return {"action": "noop", "reason": "not-newer", "from": ver_e, "to": ver_p}
    if sha_e is None or canonical_hash(text) != sha_e:
        return {"action": "stuck", "reason": "local-edit", "from": ver_e}
    new_body = canonical.read_text(encoding="utf-8")
    new_text = new_body + make_stamp(ver_p, canonical_hash(new_body))
    tmp = installed.with_name(installed.name + ".tmp")
    tmp.write_text(new_text, encoding="utf-8")
    tmp.replace(installed)
    return {"action": "refreshed", "reason": "up", "from": ver_e, "to": ver_p}
