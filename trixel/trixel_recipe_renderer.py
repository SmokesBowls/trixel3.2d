import sys
import json
import random
from pathlib import Path
from PIL import Image

class Canvas:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.pixels = [[[0, 0, 0] for _ in range(width)] for _ in range(height)]

    def set_pixel(self, x: int, y: int, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.pixels[y][x] = [int(color[0]), int(color[1]), int(color[2])]

    def save_png(self, path: Path):
        img = Image.new("RGB", (self.width, self.height))
        flat_data = []
        for y in range(self.height):
            for x in range(self.width):
                flat_data.append(tuple(self.pixels[y][x]))
        img.putdata(flat_data)
        img.save(path)
        print(f"Recipe texture saved to {path} (size: {self.width}x{self.height})")

class RecipeRenderer:
    def __init__(self, canvas: Canvas):
        self.canvas = canvas

    def execute(self, recipe: dict):
        passes = recipe.get("passes", recipe.get("actions", recipe.get("strokes", [])))
        # Filter out entity_marker for base texture generation
        terrain_passes = [p for p in passes if p.get("type") != "entity_marker"]
        
        for idx, step in enumerate(terrain_passes):
            pass_type = step.get("type", "unknown")
            if pass_type == "gradient_fill":
                self._exec_gradient_fill(step)
            elif pass_type == "noise_scatter":
                self._exec_noise_scatter(step)
            elif pass_type == "h_band":
                self._exec_h_band(step)
            elif pass_type == "v_crack":
                self._exec_v_crack(step)
            elif pass_type == "ember_scatter":
                self._exec_ember_scatter(step)
            else:
                print(f"Warning: Unknown pass type {pass_type}")

    def _exec_gradient_fill(self, step: dict):
        top = tuple(step.get("top", [30, 10, 0]))
        bottom = tuple(step.get("bottom", [80, 20, 0]))
        for y in range(self.canvas.height):
            t = y / max(1, self.canvas.height - 1)
            color = tuple(int(bottom[c] * t + top[c] * (1 - t)) for c in range(3))
            for x in range(self.canvas.width):
                self.canvas.set_pixel(x, y, color)

    def _exec_noise_scatter(self, step: dict):
        density = float(step.get("density", 0.1))
        colors = [tuple(c) for c in step.get("colors", [[255, 255, 255]])]
        rng = random.Random(step.get("seed", 0))
        for y in range(self.canvas.height):
            for x in range(self.canvas.width):
                if rng.random() < density:
                    self.canvas.set_pixel(x, y, rng.choice(colors))

    def _exec_h_band(self, step: dict):
        rng = random.Random(int(step.get("seed", 0)))
        y_value = float(step.get("y", 0.5))
        thickness_value = float(step.get("thickness", 1.0))
        color = tuple(int(c) for c in step.get("color", [255, 255, 255]))
        jitter = float(step.get("jitter", 0.0))
        waviness = float(step.get("waviness", 0.0))
        gap_chance = float(step.get("gap_chance", 0.0))

        base_y = (
            int(round(y_value * (self.canvas.height - 1)))
            if y_value <= 1.0
            else int(round(y_value))
        )
        thickness = (
            max(1, int(round(thickness_value * self.canvas.height)))
            if thickness_value <= 1.0
            else max(1, int(round(thickness_value)))
        )

        current_y = base_y
        for x in range(self.canvas.width):
            if rng.random() < waviness:
                current_y += rng.choice([-1, 0, 1])
            for dy in range(thickness):
                yy = current_y + dy
                if rng.random() < jitter:
                    yy += rng.choice([-1, 0, 1])
                if rng.random() < gap_chance:
                    continue
                if 0 <= yy < self.canvas.height:
                    self.canvas.set_pixel(x, yy, color)

    def _exec_v_crack(self, step: dict):
        rng = random.Random(int(step.get("seed", 0)))
        x_value = float(step.get("x", 0.5))
        y_start_value = float(step.get("y_start", 0.0))
        y_end_value = float(step.get("y_end", 1.0))
        color = tuple(int(c) for c in step.get("color", [255, 100, 0]))
        glow = bool(step.get("glow", False))
        glow_color = tuple(int(c) for c in step.get("glow_color", [100, 20, 0]))
        jitter = float(step.get("jitter", 0.0))
        gap_chance = float(step.get("gap_chance", 0.0))
        branch_chance = float(step.get("branch_chance", 0.0))

        cx = (
            int(round(x_value * (self.canvas.width - 1)))
            if x_value <= 1.0
            else int(round(x_value))
        )
        y_start = (
            int(round(y_start_value * (self.canvas.height - 1)))
            if y_start_value <= 1.0
            else int(round(y_start_value))
        )
        y_end = (
            int(round(y_end_value * (self.canvas.height - 1)))
            if y_end_value <= 1.0
            else int(round(y_end_value))
        )
        if y_end < y_start:
            y_start, y_end = y_end, y_start

        for y in range(y_start, y_end + 1):
            if rng.random() < jitter:
                cx += rng.choice([-1, 0, 1])
            cx = max(0, min(self.canvas.width - 1, cx))
            if rng.random() < gap_chance:
                continue

            self.canvas.set_pixel(cx, y, color)

            if rng.random() < branch_chance:
                cx += rng.choice([-1, 1])
                cx = max(0, min(self.canvas.width - 1, cx))

            if glow:
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    gx, gy = cx + dx, y + dy
                    if 0 <= gx < self.canvas.width and 0 <= gy < self.canvas.height:
                        if rng.random() < 0.4:
                            self.canvas.set_pixel(gx, gy, glow_color)

    def _exec_ember_scatter(self, step: dict):
        count = int(step.get("count", 5))
        colors = [tuple(c) for c in step.get("colors", [[255, 140, 0], [255, 215, 0]])]
        rng = random.Random(step.get("seed", 0))
        for _ in range(count):
            x = rng.randint(0, self.canvas.width - 1)
            y = rng.randint(0, self.canvas.height - 1)
            self.canvas.set_pixel(x, y, rng.choice(colors))

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 trixel_recipe_renderer.py <recipe_path> <output_png_path>")
        sys.exit(1)

    recipe_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not recipe_path.exists():
        print(f"Error: Recipe file {recipe_path} not found.")
        sys.exit(1)

    with open(recipe_path, "r") as f:
        recipe = json.load(f)

    canvas_size = recipe.get("canvas", {"width": 16, "height": 16})
    width = canvas_size.get("width", 16)
    height = canvas_size.get("height", 16)

    canvas = Canvas(width, height)
    renderer = RecipeRenderer(canvas)
    renderer.execute(recipe)
    canvas.save_png(output_path)

if __name__ == "__main__":
    main()
