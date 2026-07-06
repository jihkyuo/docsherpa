import json
from pathlib import Path

import refresh


def test_make_and_parse_stamp_roundtrip():
    s = refresh.make_stamp("0.0.2", "abc123def456")
    assert "docsherpa-scaffold: v0.0.2 sha=abc123def456" in s
    assert refresh.parse_stamp("body\n" + s) == ("0.0.2", "abc123def456")


def test_parse_old_stamp_without_sha():
    assert refresh.parse_stamp("x\n<!-- docsherpa-scaffold: v0.0.1 -->\n") == ("0.0.1", None)


def test_parse_stamp_none_when_absent():
    assert refresh.parse_stamp("no stamp here\n") is None


def test_strip_stamp_removes_trailing_stamp():
    body = "line1\nline2\n"
    text = body + refresh.make_stamp("0.0.2", "abc123def456")
    assert refresh.strip_stamp(text).rstrip("\n") == "line1\nline2"


def test_canonical_hash_ignores_stamp_and_crlf():
    a = "line1\nline2\n" + refresh.make_stamp("0.0.1", "old")
    b = "line1\r\nline2" + refresh.make_stamp("0.0.9", "different")
    assert refresh.canonical_hash(a) == refresh.canonical_hash(b)   # 스탬프·CRLF 무관


def test_version_gt_int_tuple():
    assert refresh.version_gt("0.0.2", "0.0.1") is True
    assert refresh.version_gt("0.1.0", "0.0.9") is True
    assert refresh.version_gt("0.0.1", "0.0.1") is False
    assert refresh.version_gt("0.0.1", "0.0.2") is False


def test_provenance_true_when_plugin_outside_and_named(tmp_path):
    plugin = tmp_path / "plugin"
    (plugin / ".claude-plugin").mkdir(parents=True)
    (plugin / ".claude-plugin" / "plugin.json").write_text('{"name":"docsherpa"}', encoding="utf-8")
    target = tmp_path / "repo"
    target.mkdir()
    assert refresh.verify_plugin_provenance(plugin, target) is True


def test_provenance_false_when_plugin_inside_target(tmp_path):
    # docsherpa 자기 repo(plugin==target) or 설치본만 있는 경우 → refresh 부정당
    target = tmp_path / "repo"
    (target / ".claude-plugin").mkdir(parents=True)
    (target / ".claude-plugin" / "plugin.json").write_text('{"name":"docsherpa"}', encoding="utf-8")
    assert refresh.verify_plugin_provenance(target, target) is False


def test_provenance_false_when_name_mismatch(tmp_path):
    plugin = tmp_path / "plugin"
    (plugin / ".claude-plugin").mkdir(parents=True)
    (plugin / ".claude-plugin" / "plugin.json").write_text('{"name":"evil"}', encoding="utf-8")
    target = tmp_path / "repo"
    target.mkdir()
    assert refresh.verify_plugin_provenance(plugin, target) is False
