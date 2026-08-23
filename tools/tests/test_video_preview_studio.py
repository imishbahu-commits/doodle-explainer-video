from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).parents[1] / "video_preview_studio.py"
SPEC = importlib.util.spec_from_file_location("video_preview_studio", MODULE_PATH)
assert SPEC and SPEC.loader
studio = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(studio)


class VideoPreviewStudioTests(unittest.TestCase):
    def test_safe_filename(self) -> None:
        self.assertEqual(studio.safe_filename("../../Final Cut (3).mp4"), "Final-Cut-3-.mp4")
        self.assertEqual(studio.safe_filename(""), "preview.mp4")

    def test_safe_upload_id(self) -> None:
        self.assertEqual(studio.safe_upload_id("abc/../../DEF-_123"), "abcDEF-_123")

    def test_parse_range(self) -> None:
        self.assertEqual(studio.parse_range("bytes=10-19", 100), (10, 19))
        self.assertEqual(studio.parse_range("bytes=90-", 100), (90, 99))
        self.assertEqual(studio.parse_range("bytes=-12", 100), (88, 99))
        self.assertIsNone(studio.parse_range(None, 100))
        with self.assertRaises(ValueError):
            studio.parse_range("bytes=100-120", 100)

    def test_inventory_lists_only_supported_video_files(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            projects = root / "projects"
            uploads = root / "uploads"
            projects.mkdir()
            uploads.mkdir()
            (projects / "sample.mp4").write_bytes(b"video")
            (projects / "notes.txt").write_text("not video")
            (uploads / "second.webm").write_bytes(b"video2")
            with mock.patch.object(studio, "ROOT", root), \
                 mock.patch.object(studio, "PROJECTS_ROOT", projects), \
                 mock.patch.object(studio, "VIDEOS_ROOT", uploads):
                items, lookup = studio.inventory()
            self.assertEqual(len(items), 2)
            self.assertEqual(len(lookup), 2)
            self.assertEqual({item["source"] for item in items}, {"Project", "Uploaded"})


if __name__ == "__main__":
    unittest.main()
