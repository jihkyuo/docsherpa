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
    body = strip_stamp(text).lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")
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
