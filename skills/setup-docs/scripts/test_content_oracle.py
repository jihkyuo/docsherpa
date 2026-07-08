import sys
import json
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import content_oracle as co


def _write(root, name, body):
    p = Path(root) / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")


class SegmentTests(unittest.TestCase):
    def test_splits_on_blank_lines(self):
        self.assertEqual(co.segment("alpha\n\nbeta"), ["alpha", "beta"])

    def test_code_fence_kept_intact(self):
        segs = co.segment("```\nx\n\ny\n```")
        self.assertEqual(len(segs), 1)
        self.assertIn("x", segs[0])
        self.assertIn("y", segs[0])

    def test_normalize_strips_link_url(self):
        self.assertEqual(co.normalize("see [docs](a/b.md) now"), "see docs now")

    def test_seg_key_stable_across_link_rewrite(self):
        a = co.seg_key("see [docs](old/path.md) now")
        b = co.seg_key("see [docs](new/place.md) now")
        self.assertEqual(a, b)


class CollectTests(unittest.TestCase):
    def test_collect_ignores_dir_named_dot_md(self):
        # rglob("*.md")는 .md로 끝나는 디렉터리도 매칭 → read_text에서 IsADirectoryError 크래시.
        with tempfile.TemporaryDirectory() as root:
            (Path(root) / "weird.md").mkdir()
            _write(root, "a.md", "hello world")
            out = co.collect(root)
            self.assertEqual(len(out), 1)


class CheckTests(unittest.TestCase):
    def _check(self, base_files, cur_files, manifest=None):
        with tempfile.TemporaryDirectory() as base, tempfile.TemporaryDirectory() as cur, tempfile.TemporaryDirectory() as md:
            for n, b in base_files.items():
                _write(base, n, b)
            for n, b in cur_files.items():
                _write(cur, n, b)
            mpath = None
            if manifest is not None:
                mpath = Path(md) / "m.json"
                mpath.write_text(json.dumps(manifest))
            args = co.argparse.Namespace(base=base, current=cur, manifest=str(mpath) if mpath else None)
            return co.cmd_check(args)

    def test_pass_on_pure_move(self):
        # 같은 내용이 다른 경로로 이동 → PASS
        rc = self._check({"a.md": "hello world\n\nsecond block"},
                         {"sub/b.md": "hello world\n\nsecond block"})
        self.assertEqual(rc, 0)

    def test_fail_on_silent_drop(self):
        # 한 블록이 매니페스트 없이 사라짐 → FAIL
        rc = self._check({"a.md": "keep me\n\ndrop me"},
                         {"a.md": "keep me"})
        self.assertEqual(rc, 1)

    def test_pass_on_declared_drop(self):
        key = co.seg_key("drop me")
        rc = self._check({"a.md": "keep me\n\ndrop me"},
                         {"a.md": "keep me"},
                         manifest={"dropped": [{"key": key, "reason": "구식"}]})
        self.assertEqual(rc, 0)

    def test_fail_on_drop_without_reason(self):
        key = co.seg_key("drop me")
        rc = self._check({"a.md": "keep me\n\ndrop me"},
                         {"a.md": "keep me"},
                         manifest={"dropped": [{"key": key, "reason": ""}]})
        self.assertEqual(rc, 1)

    def test_pass_on_transformed(self):
        key = co.seg_key("old phrasing here")
        rc = self._check({"a.md": "old phrasing here"},
                         {"a.md": "rewritten phrasing entirely"},
                         manifest={"transformed": [{"key": key, "to": "rewritten phrasing entirely"}]})
        self.assertEqual(rc, 0)

    def test_fail_on_transform_with_absent_destination(self):
        # to 값이 current에 없으면 → FAIL (내용 유실 세탁 차단)
        key = co.seg_key("old phrasing here")
        rc = self._check({"a.md": "old phrasing here"},
                         {"a.md": "completely unrelated text"},
                         manifest={"transformed": [{"key": key, "to": "something that is not in current"}]})
        self.assertEqual(rc, 1)

    def test_fail_on_transform_with_empty_to(self):
        # to 값이 빈 문자열이면 → FAIL
        key = co.seg_key("old phrasing here")
        rc = self._check({"a.md": "old phrasing here"},
                         {"a.md": "completely unrelated text"},
                         manifest={"transformed": [{"key": key, "to": ""}]})
        self.assertEqual(rc, 1)


class InvalidByteTests(unittest.TestCase):
    def test_collect_surfaces_dropped_invalid_utf8_bytes(self):
        # invalid UTF-8 바이트가 current에서 소실되면 base 세그먼트 key가 달라져
        # 오라클이 unaccounted로 잡아야 한다. errors="ignore"면 양쪽 다 바이트를
        # 버려 차이가 안 보이는 사각(G2) — surrogateescape로 바이트를 key에 반영.
        with tempfile.TemporaryDirectory() as base, tempfile.TemporaryDirectory() as cur:
            (Path(base) / "a.md").write_bytes(
                "keep this segment ".encode("utf-8") + b"\xff" + "unique-marker".encode("utf-8"))
            (Path(cur) / "a.md").write_bytes(
                "keep this segment unique-marker".encode("utf-8"))   # 바이트 소실판
            base_keys = set(co.collect(base))
            cur_keys = set(co.collect(cur))
            self.assertTrue(base_keys - cur_keys)   # 최소 하나 unaccounted(소실 감지)

    def test_collect_preview_is_strict_utf8_encodable(self):
        # preview는 표시용(cmd_keys/cmd_check가 print) — lone surrogate가 남으면
        # strict stdout(PYTHONIOENCODING=utf-8:strict 등)에서 print가 크래시한다.
        # key는 정확 바이트를 담되, preview는 표시-안전해야(surrogateescape 후속).
        with tempfile.TemporaryDirectory() as base:
            (Path(base) / "a.md").write_bytes("seg ".encode("utf-8") + b"\xff" + "mark".encode("utf-8"))
            for e in co.collect(base).values():
                e["preview"].encode("utf-8")   # strict — surrogate면 UnicodeEncodeError


if __name__ == "__main__":
    unittest.main()
