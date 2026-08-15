import vsketch
from shapely.geometry import LineString


class FlowSketch(vsketch.SketchClass):
    """Signature vsketch demo: flowing line art + wobbly contours.

    This is what vsketch is FOR: generative pen-plotter style abstract art —
    thousands of organic lines, parametric, reproducible. It does NOT draw
    characters."""

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("1376x768", landscape=True)
        vsk.scale("px")

        # --- flowing ribbon lines (like current/water/wind) ------------
        for i in range(120):
            vsk.stroke(i + 1)
            x0 = vsk.random(0, 1376)
            pts = []
            for j in range(60):
                x = x0 + j * 18 + vsk.noise(j * 0.06, i * 0.5) * 60
                y = vsk.noise(j * 0.04, i * 0.7 + 3) * 768 + vsk.random(-8, 8)
                pts.append((x, y))
            vsk.geometry(LineString(pts))

        # --- hand-wobbled contour ellipses ------------------------------
        for i in range(24):
            vsk.stroke(2)
            cx, cy = vsk.random(80, 1296), vsk.random(80, 688)
            rx, ry = vsk.random(40, 130), vsk.random(30, 90)
            vsk.ellipse(cx, cy, rx, ry, mode="radius")

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    FlowSketch.display()
