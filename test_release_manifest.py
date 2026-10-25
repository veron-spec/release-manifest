import json
import tempfile
import unittest
from pathlib import Path

from release_manifest import build_manifest, main, verify


class ReleaseManifestTests(unittest.TestCase):
    def test_manifest_is_deterministic_and_excludes_itself(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "z.txt").write_text("z", encoding="utf-8")
            (root / "a.txt").write_text("a", encoding="utf-8")
            first = build_manifest(root, "manifest.json")
            second = build_manifest(root, "manifest.json")
            self.assertEqual(first, second)
            self.assertEqual([item["path"] for item in first["files"]], ["a.txt", "z.txt"])

    def test_verify_detects_change_missing_and_unexpected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "keep.txt").write_text("original", encoding="utf-8")
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps(build_manifest(root, "manifest.json")), encoding="utf-8")
            (root / "keep.txt").write_text("changed", encoding="utf-8")
            (root / "extra.txt").write_text("extra", encoding="utf-8")
            self.assertEqual(verify(root, manifest), ["unexpected: extra.txt", "changed: keep.txt", "size changed: keep.txt"])

    def test_invalid_root_returns_two(self):
        self.assertEqual(main(["missing-directory"]), 2)


if __name__ == "__main__":
    unittest.main()
