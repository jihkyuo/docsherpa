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


def test_parse_stamp_takes_trailing_when_body_has_example():
    text = ("docs mention <!-- docsherpa-scaffold: v9.9.9 sha=999999999999 --> as an example\n"
            "body\n" + refresh.make_stamp("0.0.2", "abc123def456"))
    assert refresh.parse_stamp(text) == ("0.0.2", "abc123def456")


def test_strip_stamp_removes_trailing_stamp():
    body = "line1\nline2\n"
    text = body + refresh.make_stamp("0.0.2", "abc123def456")
    assert refresh.strip_stamp(text).rstrip("\n") == "line1\nline2"


def test_canonical_hash_ignores_stamp_and_crlf():
    a = "line1\nline2\n" + refresh.make_stamp("0.0.1", "old")
    b = "line1\r\nline2" + refresh.make_stamp("0.0.9", "different")
    assert refresh.canonical_hash(a) == refresh.canonical_hash(b)   # 스탬프·CRLF 무관


def test_canonical_hash_stable_across_trailing_whitespace_and_stamp():
    body = "hello world   \n"          # trailing spaces before newline
    stamped = body + refresh.make_stamp("0.0.2", "abc123def456")
    # canonical_hash of the bare body must equal that of the stamped file
    assert refresh.canonical_hash(body) == refresh.canonical_hash(stamped)


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


def _fake_plugin(tmp_path, version, skill_body):
    plugin = tmp_path / "plugin"
    (plugin / ".claude-plugin").mkdir(parents=True)
    (plugin / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": "docsherpa", "version": version}), encoding="utf-8")
    dr = plugin / "skills" / "doc-reconcile"
    dr.mkdir(parents=True)
    (dr / "SKILL.md").write_text(skill_body, encoding="utf-8")
    return plugin


def _install(repo, body, version, sha):
    dst = repo / ".claude" / "skills" / "doc-reconcile" / "SKILL.md"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(body + refresh.make_stamp(version, sha), encoding="utf-8")
    return dst


def test_refresh_upgrades_installed_to_new_version(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    old = "old skill v1 body\n"
    _install(repo, old, "0.0.1", refresh.canonical_hash(old))
    new = "NEW skill v2 body\n"
    plugin = _fake_plugin(tmp_path, "0.0.2", new)
    res = refresh.refresh_loop(repo, plugin)
    assert res["action"] == "refreshed" and res["to"] == "0.0.2"
    installed = (repo / ".claude/skills/doc-reconcile/SKILL.md").read_text(encoding="utf-8")
    assert "NEW skill v2 body" in installed
    assert refresh.parse_stamp(installed) == ("0.0.2", refresh.canonical_hash(new))


def test_refresh_noop_on_downgrade(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    body = "current body\n"
    _install(repo, body, "0.0.5", refresh.canonical_hash(body))
    plugin = _fake_plugin(tmp_path, "0.0.2", "older body\n")
    assert refresh.refresh_loop(repo, plugin)["action"] == "noop"
    assert "current body" in (repo / ".claude/skills/doc-reconcile/SKILL.md").read_text(encoding="utf-8")


def test_refresh_noop_on_same_version(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    body = "body\n"
    _install(repo, body, "0.0.2", refresh.canonical_hash(body))
    plugin = _fake_plugin(tmp_path, "0.0.2", "different body\n")
    assert refresh.refresh_loop(repo, plugin)["action"] == "noop"


def test_refresh_stuck_when_locally_edited(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    body = "original body\n"
    # 설치본을 사용자가 편집: 기록된 sha는 original인데 내용은 바뀜
    _install(repo, "USER EDITED body\n", "0.0.1", refresh.canonical_hash(body))
    plugin = _fake_plugin(tmp_path, "0.0.2", "plugin new body\n")
    res = refresh.refresh_loop(repo, plugin)
    assert res["action"] == "stuck"
    assert "USER EDITED body" in (repo / ".claude/skills/doc-reconcile/SKILL.md").read_text(encoding="utf-8")


def test_refresh_noop_when_plugin_inside_target(tmp_path):
    # 설치본만 있는 repo(플러그인 없음) 시뮬 — plugin_root를 repo 자신으로 줌 → provenance no-op
    repo = tmp_path / "repo"; repo.mkdir()
    (repo / ".claude-plugin").mkdir()
    (repo / ".claude-plugin" / "plugin.json").write_text('{"name":"docsherpa","version":"9.9.9"}', encoding="utf-8")
    body = "body\n"
    _install(repo, body, "0.0.1", refresh.canonical_hash(body))
    assert refresh.refresh_loop(repo, repo)["action"] == "noop"


def test_refresh_stuck_on_old_stamp_without_sha(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    dst = repo / ".claude" / "skills" / "doc-reconcile" / "SKILL.md"
    dst.parent.mkdir(parents=True)
    dst.write_text("body\n<!-- docsherpa-scaffold: v0.0.1 -->\n", encoding="utf-8")  # sha 없음
    plugin = _fake_plugin(tmp_path, "0.0.2", "new\n")
    assert refresh.refresh_loop(repo, plugin)["action"] == "stuck"


def test_canonical_doc_reconcile_is_stampless():
    canonical = Path(__file__).resolve().parents[2] / "doc-reconcile" / "SKILL.md"
    assert refresh.parse_stamp(canonical.read_text(encoding="utf-8")) is None, (
        "canonical doc-reconcile SKILL must have NO scaffold stamp — a trailing stamp would "
        "make refresh double-stamp and falsely mark all downstream installs 'stuck'")


def test_refresh_twice_across_two_upgrades(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    v1 = "body one\n"
    _install(repo, v1, "0.0.1", refresh.canonical_hash(v1))
    p2 = _fake_plugin(tmp_path, "0.0.2", "body two\n")
    assert refresh.refresh_loop(repo, p2)["action"] == "refreshed"
    # now upgrade the SAME plugin dir to 0.0.3 with new body, refresh again
    (p2 / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": "docsherpa", "version": "0.0.3"}), encoding="utf-8")
    (p2 / "skills" / "doc-reconcile" / "SKILL.md").write_text("body three\n", encoding="utf-8")
    res = refresh.refresh_loop(repo, p2)
    assert res["action"] == "refreshed" and res["to"] == "0.0.3"   # not falsely 'stuck'
    assert "body three" in (repo / ".claude/skills/doc-reconcile/SKILL.md").read_text(encoding="utf-8")
