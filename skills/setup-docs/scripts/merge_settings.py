"""SessionStart 훅 멱등 병합 — 기존 settings.json을 보존하며 doc-drift prime 훅만 추가.

spec R1의 3-파트 계약: dedup 술어(_norm) + 포맷 보존(최소 침습) + 파일 선택(settings.json, .local 아님).
"""
import json
from pathlib import Path


def _norm(command: str) -> str:
    """경로·따옴표·./ 차이를 무시한 dedup 키."""
    return " ".join(command.replace("./", "").replace('"', "").split())


def merge_hook(settings: dict, command: str):
    """(갱신된 settings, changed?) 반환. 동일(정규화) 훅이 이미 있으면 changed=False."""
    hooks = settings.setdefault("hooks", {})
    sessionstart = hooks.setdefault("SessionStart", [])
    for entry in sessionstart:
        for h in entry.get("hooks", []):
            if h.get("type") == "command" and _norm(h.get("command", "")) == _norm(command):
                return settings, False
    sessionstart.append({"hooks": [{"type": "command", "command": command}]})
    return settings, True


def merge_settings_file(claude_dir, command: str) -> bool:
    """.claude/settings.json(공유)만 대상. 없으면 생성. (.local엔 절대 안 씀.) changed? 반환.

    ⚠️ json.load→dump라 주석·키순서를 재작성한다 — settings.json이 표준 JSON일 때만 무손실.
    JSONC(주석 허용)면 M3에서 comment-preserving 편집으로 승격(spike T2 Step 11 결정).
    """
    path = Path(claude_dir) / "settings.json"
    settings = json.loads(path.read_text()) if path.exists() else {}
    settings, changed = merge_hook(settings, command)
    if changed:
        path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n")
    return changed
