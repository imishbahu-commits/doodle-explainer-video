from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "reference_upload_server.py"
SPEC = importlib.util.spec_from_file_location("reference_upload_server", MODULE_PATH)
assert SPEC and SPEC.loader
studio = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(studio)


class ReferenceUploadServerTests(unittest.TestCase):
    def test_safe_filename_removes_paths_and_unsafe_characters(self) -> None:
        self.assertEqual(studio.safe_filename("../../My Video (final).mp4"), "My-Video-final-.mp4")
        self.assertEqual(studio.safe_filename(""), "reference.mp4")

    def test_safe_project_id_is_restricted(self) -> None:
        self.assertEqual(studio.safe_project_id("abc/../../DEF-_123"), "abcDEF-_123")

    def test_atomic_json_is_valid_and_replaces_target(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "manifest.json"
            studio.atomic_json(path, {"version": 1})
            studio.atomic_json(path, {"version": 2})
            self.assertEqual(json.loads(path.read_text()), {"version": 2})
            self.assertFalse(path.with_suffix(".json.tmp").exists())

    def test_parse_media_info_from_sample_when_available(self) -> None:
        sample = MODULE_PATH.parents[1] / "projects" / "expressive-tickle-sample" / "expressive-tickle-sample.mp4"
        if not sample.exists():
            self.skipTest("sample video is not present")
        info = studio.parse_media_info(sample)
        self.assertGreater(info["duration_seconds"], 39)
        self.assertEqual(info["width"], 1920)
        self.assertEqual(info["height"], 1080)
        self.assertAlmostEqual(info["fps"], 30, places=1)


if __name__ == "__main__":
    unittest.main()
