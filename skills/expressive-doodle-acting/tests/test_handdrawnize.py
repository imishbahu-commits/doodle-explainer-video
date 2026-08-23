from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "handdrawnize.py"
SPEC = importlib.util.spec_from_file_location("handdrawnize", MODULE_PATH)
assert SPEC and SPEC.loader
handdrawnize = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(handdrawnize)


class HanddrawnizeTests(unittest.TestCase):
    def fixture(self) -> Image.Image:
        image = Image.new("RGBA", (180, 140), (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse((35, 12, 145, 112), fill=(238, 184, 132, 255))
        draw.polygon([(55, 36), (86, 5), (110, 40), (135, 8), (145, 50)], fill=(55, 38, 27, 255))
        draw.ellipse((62, 55, 75, 68), fill=(15, 15, 15, 255))
        draw.ellipse((108, 55, 121, 68), fill=(15, 15, 15, 255))
        draw.arc((70, 66, 112, 94), 0, 180, fill=(70, 25, 25, 255), width=3)
        return image

    def render(self, seed: int) -> tuple[Image.Image, Image.Image]:
        source = self.fixture()
        alpha = source.getchannel("A")
        flat = handdrawnize.flatten_rgb(source, 7, 3)
        edges = handdrawnize.region_edges(flat, alpha, 28)
        mask = handdrawnize.make_ink_mask(edges, 3, 1.2, seed, 246)
        return handdrawnize.composite_ink(flat, alpha, mask, handdrawnize.INK), mask

    def test_same_seed_is_byte_deterministic(self) -> None:
        first, first_mask = self.render(17)
        second, second_mask = self.render(17)
        self.assertEqual(first.tobytes(), second.tobytes())
        self.assertEqual(first_mask.tobytes(), second_mask.tobytes())

    def test_seed_changes_imperfection_not_dimensions(self) -> None:
        first, _ = self.render(17)
        second, _ = self.render(18)
        self.assertEqual(first.size, second.size)
        self.assertNotEqual(first.tobytes(), second.tobytes())

    def test_output_preserves_transparency_and_adds_silhouette_ink(self) -> None:
        out, mask = self.render(17)
        alpha = out.getchannel("A")
        self.assertEqual(alpha.getpixel((0, 0)), 0)
        mask_values = mask.get_flattened_data() if hasattr(mask, "get_flattened_data") else mask.getdata()
        alpha_values = alpha.get_flattened_data() if hasattr(alpha, "get_flattened_data") else alpha.getdata()
        self.assertGreater(max(mask_values), 0)
        self.assertGreater(sum(1 for p in alpha_values if p > 0), 1000)

    def test_metrics_are_json_serializable(self) -> None:
        out, mask = self.render(17)
        data = handdrawnize.metrics(out.convert("RGB"), out.getchannel("A"), mask, 7)
        encoded = json.dumps(data)
        self.assertIn("ink_coverage", encoded)


if __name__ == "__main__":
    unittest.main()
