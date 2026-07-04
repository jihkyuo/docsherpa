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


if __name__ == "__main__":
    unittest.main()
