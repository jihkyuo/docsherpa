"""SessionStart 훅 멱등 병합 — 기존 settings.json을 보존하며 doc-drift prime 훅만 추가.

spec R1의 3-파트 계약: dedup 술어(_norm) + 포맷 보존(최소 침습) + 파일 선택(settings.json, .local 아님).
JSONC(주석)면 comment-preserving을 짓지 않고 fail-safe로 거부한다(M3 결정 — settings는 표준 JSON이 정상, YAGNI).
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

    표준 JSON만 무손실 병합한다. 주석(JSONC) 등으로 파싱 실패하면 파일을 건드리지 않고
    ValueError로 수동 병합을 안내한다(클로버·크래시 대신 fail-safe — spec §14 JSONC 결정:
    comment-preserving을 짓지 않고 거부한다. settings는 표준 JSON이 정상, YAGNI).
    """
    path = Path(claude_dir) / "settings.json"
    if path.exists():
        try:
            settings = json.loads(path.read_text())
        except json.JSONDecodeError:
            raise ValueError(
                f"{path} 가 표준 JSON이 아니다(주석/JSONC 추정). 자동 병합을 건너뛴다 — "
                f"SessionStart 훅을 수동으로 추가하라(merge this hook manually): {command}"
            )
    else:
        settings = {}
    settings, changed = merge_hook(settings, command)
    if changed:
        path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n")
    return changed
