import json
import pytest
from merge_settings import merge_hook, merge_settings_file


def test_preserves_existing_sessionstart_hook():
    settings = {
        "hooks": {
            "SessionStart": [
                {"hooks": [{"type": "command", "command": "echo user-env-setup"}]}
            ]
        }
    }
    out, changed = merge_hook(settings, "cat .claude/doc-drift-prime.txt 2>/dev/null || true")
    cmds = [h["command"]
            for entry in out["hooks"]["SessionStart"]
            for h in entry["hooks"]]
    assert "echo user-env-setup" in cmds            # 기존 보존
    assert any("doc-drift-prime.txt" in c for c in cmds)  # 새 훅 추가
    assert changed is True


def test_idempotent_across_path_notation():
    settings = {}
    settings, c1 = merge_hook(settings, "cat .claude/doc-drift-prime.txt 2>/dev/null || true")
    settings, c2 = merge_hook(settings, "cat ./.claude/doc-drift-prime.txt 2>/dev/null || true")  # ./ 표기차
    assert c1 is True and c2 is False               # 두 번째는 dedup
    total = sum(len(e["hooks"]) for e in settings["hooks"]["SessionStart"])
    assert total == 1                                # 중복 append 없음


def test_writes_to_settings_json_not_local(tmp_path):
    claude = tmp_path / ".claude"
    claude.mkdir()
    (claude / "settings.json").write_text(
        '{"hooks":{"SessionStart":[{"hooks":[{"type":"command","command":"echo keep"}]}]}}'
    )
    merge_settings_file(claude, "cat .claude/doc-drift-prime.txt 2>/dev/null || true")
    data = json.loads((claude / "settings.json").read_text())
    cmds = [h["command"] for e in data["hooks"]["SessionStart"] for h in e["hooks"]]
    assert "echo keep" in cmds and any("doc-drift-prime" in c for c in cmds)
    assert not (claude / "settings.local.json").exists()   # .local 건드리지 않음


def test_jsonc_with_comments_refuses_without_clobber(tmp_path):
    claude = tmp_path / ".claude"
    claude.mkdir()
    original = '{\n  // user comment\n  "hooks": {}\n}\n'
    (claude / "settings.json").write_text(original)
    with pytest.raises(ValueError) as exc:
        merge_settings_file(claude, "cat .claude/doc-drift-prime.txt 2>/dev/null || true")
    assert "manually" in str(exc.value).lower() or "수동" in str(exc.value)
    # 파일은 절대 손상되지 않는다 (클로버 금지)
    assert (claude / "settings.json").read_text() == original
