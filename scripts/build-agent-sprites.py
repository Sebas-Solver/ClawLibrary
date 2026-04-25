#!/usr/bin/env python3
"""
Build Agent Spritesheets v4
===========================
Simplified pipeline: New generated sprites have clean transparent backgrounds.
Just detect individual character poses, extract, normalize to 128x128, and
build ping-pong animation strips.
"""

from PIL import Image
import os
import json

FRAME_SIZE = 128
ARTIFACTS_DIR = os.path.expanduser(
    "~/.gemini/antigravity/brain/5afb264b-9935-4d91-82a1-b4fda7280027"
)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACTORS_DIR = os.path.join(PROJECT_ROOT, "public", "assets", "generated", "actors")

# New naming convention: character_action_sprites_*.png
AGENTS = {
    "kora-robot-v1": {
        "stand_front": "kora_idle_sprites",
        "walk": "kora_walk_sprites",
        "work": "kora_work_sprites",
    },
    "sumi-secretary-v1": {
        "stand_front": "sumi_idle_sprites",
        "walk": "sumi_walk_sprites",
        "work": "sumi_work_sprites",
    },
    "gael-doctor-v1": {
        "stand_front": "gael_idle_sprites",
        "walk": "gael_walk_sprites",
        "work": "gael_work_sprites",
    },
}


def find_source_image(pattern: str) -> str | None:
    """Find the most recent matching source image."""
    candidates = []
    for f in os.listdir(ARTIFACTS_DIR):
        if f.startswith(pattern) and f.endswith(".png"):
            candidates.append(os.path.join(ARTIFACTS_DIR, f))
    if not candidates:
        return None
    return max(candidates, key=os.path.getmtime)


def color_dist(c1, c2):
    """Euclidean distance between two RGB tuples."""
    return ((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2 + (c1[2]-c2[2])**2) ** 0.5


def remove_checker_background(img: Image.Image) -> Image.Image:
    """
    Remove the visual checkerboard transparency indicator.
    The generated images show a gray/white checkerboard where transparent pixels
    should be. This detects and removes it via edge flood-fill.
    """
    img = img.convert("RGBA")
    pixels = img.load()
    w, h = img.size

    # Sample corner to detect checker colors
    corner_colors = set()
    for y in range(min(20, h)):
        for x in range(min(20, w)):
            r, g, b, a = pixels[x, y]
            if a > 200:
                corner_colors.add((r, g, b))

    if not corner_colors:
        return img

    # Find the two dominant checker colors
    # Sort by luminance and cluster
    samples = list(corner_colors)
    samples.sort(key=lambda c: c[0] + c[1] + c[2])
    
    # Get the darkest and lightest from corners
    # Typical checker: ~(191,191,191) and ~(255,255,255) or similar grays
    dark_bg = samples[0]
    light_bg = samples[-1]
    
    # Verify they're actually gray-ish (checker pattern)
    def is_grayish(c):
        return abs(c[0] - c[1]) < 20 and abs(c[1] - c[2]) < 20
    
    if not (is_grayish(dark_bg) and is_grayish(light_bg)):
        # Not a standard checker - skip
        return img

    TOLERANCE = 20

    def matches_bg(r, g, b, a):
        if a < 10:
            return True
        if not is_grayish((r, g, b)):
            return False
        if color_dist((r, g, b), dark_bg) < TOLERANCE:
            return True
        if color_dist((r, g, b), light_bg) < TOLERANCE:
            return True
        return False

    # Flood-fill from edges
    from collections import deque
    visited = set()
    queue = deque()

    # Seed from all edges
    for x in range(w):
        for y in [0, 1, h-1, h-2]:
            if (x, y) not in visited:
                r, g, b, a = pixels[x, y]
                visited.add((x, y))
                if matches_bg(r, g, b, a):
                    pixels[x, y] = (0, 0, 0, 0)
                    queue.append((x, y))
    for y in range(h):
        for x in [0, 1, w-1, w-2]:
            if (x, y) not in visited:
                r, g, b, a = pixels[x, y]
                visited.add((x, y))
                if matches_bg(r, g, b, a):
                    pixels[x, y] = (0, 0, 0, 0)
                    queue.append((x, y))

    while queue:
        x, y = queue.popleft()
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)]:
            nx, ny = x+dx, y+dy
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in visited:
                visited.add((nx, ny))
                r, g, b, a = pixels[nx, ny]
                if matches_bg(r, g, b, a):
                    pixels[nx, ny] = (0, 0, 0, 0)
                    queue.append((nx, ny))

    return img


def find_content_bounds(img: Image.Image) -> tuple[int, int, int, int] | None:
    """Find the bounding box of all non-transparent content."""
    pixels = img.load()
    w, h = img.size
    min_x, min_y, max_x, max_y = w, h, 0, 0
    found = False
    for y in range(h):
        for x in range(w):
            if pixels[x, y][3] > 30:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
                found = True
    if not found:
        return None
    return (min_x, min_y, max_x + 1, max_y + 1)


def detect_character_regions(img: Image.Image, expected: int = 4) -> list[tuple[int,int,int,int]]:
    """
    Detect individual character regions by finding vertical gaps
    in content columns.
    """
    pixels = img.load()
    w, h = img.size

    # Calculate alpha per column
    col_content = []
    for x in range(w):
        count = 0
        for y in range(h):
            if pixels[x, y][3] > 30:
                count += 1
        col_content.append(count)

    # Find contiguous content columns (with small gap tolerance)
    threshold = h * 0.01  # 1% content threshold
    content_cols = [c > threshold for c in col_content]
    
    # Smooth: fill gaps smaller than 5px 
    for i in range(2, w - 2):
        if not content_cols[i] and content_cols[i-2] and content_cols[i+2]:
            content_cols[i] = True

    # Find runs of content
    regions_x = []
    in_run = False
    start = 0
    for x in range(w):
        if content_cols[x] and not in_run:
            start = x
            in_run = True
        elif not content_cols[x] and in_run:
            regions_x.append((start, x))
            in_run = False
    if in_run:
        regions_x.append((start, w))

    # Do the same for rows to get vertical bounds
    row_content = []
    for y in range(h):
        count = 0
        for x in range(w):
            if pixels[x, y][3] > 30:
                count += 1
        row_content.append(count)

    content_rows = [c > w * 0.005 for c in row_content]
    regions_y = []
    in_run = False
    for y in range(h):
        if content_rows[y] and not in_run:
            start = y
            in_run = True
        elif not content_rows[y] and in_run:
            regions_y.append((start, y))
            in_run = False
    if in_run:
        regions_y.append((start, h))

    print(f"    Layout: {len(regions_x)} cols × {len(regions_y)} rows")

    regions = []
    
    if len(regions_x) >= expected and len(regions_y) >= 1:
        # Single row or use first row
        y1, y2 = regions_y[0] if regions_y else (0, h)
        for x1, x2 in regions_x[:expected]:
            # Get tight bounds within this column
            bx1, by1, bx2, by2 = x2, y2, x1, y1
            for y in range(y1, y2):
                for x in range(x1, x2):
                    if pixels[x, y][3] > 30:
                        bx1 = min(bx1, x)
                        by1 = min(by1, y)
                        bx2 = max(bx2, x)
                        by2 = max(by2, y)
            if bx2 > bx1:
                regions.append((bx1, by1, bx2 + 1, by2 + 1))
    
    elif len(regions_x) >= 2 and len(regions_y) >= 2:
        # Grid layout (e.g. 2x2)
        for y1, y2 in regions_y:
            for x1, x2 in regions_x:
                bx1, by1, bx2, by2 = x2, y2, x1, y1
                for y in range(y1, y2):
                    for x in range(x1, x2):
                        if pixels[x, y][3] > 30:
                            bx1 = min(bx1, x)
                            by1 = min(by1, y)
                            bx2 = max(bx2, x)
                            by2 = max(by2, y)
                if bx2 > bx1:
                    regions.append((bx1, by1, bx2 + 1, by2 + 1))
                if len(regions) >= expected:
                    break
            if len(regions) >= expected:
                break

    if len(regions) < expected:
        # Fallback: divide evenly
        if expected == 4:
            cw, ch = w // 2, h // 2
            cells = [(0, 0, cw, ch), (cw, 0, w, ch), (0, ch, cw, h), (cw, ch, w, h)]
            regions = []
            for cx1, cy1, cx2, cy2 in cells:
                bx1, by1, bx2, by2 = cx2, cy2, cx1, cy1
                for y in range(cy1, cy2):
                    for x in range(cx1, cx2):
                        if pixels[x, y][3] > 30:
                            bx1 = min(bx1, x)
                            by1 = min(by1, y)
                            bx2 = max(bx2, x)
                            by2 = max(by2, y)
                if bx2 > bx1:
                    regions.append((bx1, by1, bx2 + 1, by2 + 1))

    return regions[:expected]


def extract_frame(img: Image.Image, bbox: tuple[int,int,int,int]) -> Image.Image:
    """Extract and center a character in a clean FRAME_SIZE × FRAME_SIZE frame."""
    x1, y1, x2, y2 = bbox
    char_img = img.crop((x1, y1, x2, y2))
    cw, ch = char_img.size

    if cw < 3 or ch < 3:
        return Image.new("RGBA", (FRAME_SIZE, FRAME_SIZE), (0, 0, 0, 0))

    # Scale to ~85% of the frame
    usable = int(FRAME_SIZE * 0.85)
    scale = min(usable / cw, usable / ch)
    new_w = max(1, int(cw * scale))
    new_h = max(1, int(ch * scale))

    # Use NEAREST for pixel art look
    char_img = char_img.resize((new_w, new_h), Image.Resampling.NEAREST)

    # Center horizontally, align bottom
    frame = Image.new("RGBA", (FRAME_SIZE, FRAME_SIZE), (0, 0, 0, 0))
    ox = (FRAME_SIZE - new_w) // 2
    oy = FRAME_SIZE - new_h - 6
    frame.paste(char_img, (ox, oy), char_img)

    return frame


def build_spritesheet(frames: list[Image.Image]) -> tuple[Image.Image, int]:
    """Build single-row spritesheet with ping-pong animation."""
    if len(frames) > 2:
        sequence = list(frames) + list(reversed(frames[1:-1]))
    else:
        sequence = list(frames)

    total_w = len(sequence) * FRAME_SIZE
    sheet = Image.new("RGBA", (total_w, FRAME_SIZE), (0, 0, 0, 0))
    for i, frame in enumerate(sequence):
        sheet.paste(frame, (i * FRAME_SIZE, 0), frame)

    return sheet, len(sequence)


def process_all():
    print("=" * 60)
    print("Build Agent Spritesheets v4")
    print("=" * 60)

    manifest_data = {}

    for agent_id, modes in AGENTS.items():
        print(f"\n▶ {agent_id}")
        output_dir = os.path.join(ACTORS_DIR, agent_id, "sheets")
        os.makedirs(output_dir, exist_ok=True)

        agent_manifest = {}

        for mode, pattern in modes.items():
            print(f"  📋 {mode}")

            src = find_source_image(pattern)
            if not src:
                print(f"    ⚠ No source found for {pattern}")
                continue

            img = Image.open(src).convert("RGBA")
            print(f"    Source: {os.path.basename(src)} ({img.size[0]}x{img.size[1]})")

            # Remove checkerboard background if present
            img = remove_checker_background(img)

            # Detect character regions
            regions = detect_character_regions(img)
            print(f"    Found {len(regions)} character regions")

            if not regions:
                print(f"    ⚠ No characters detected, skipping")
                continue

            # Extract and normalize frames
            frames = [extract_frame(img, r) for r in regions]

            # Build spritesheet
            sheet, frame_count = build_spritesheet(frames)

            # Save
            out_path = os.path.join(output_dir, f"{mode}-spritesheet.png")
            sheet.save(out_path, "PNG")
            print(f"    ✓ Saved: {sheet.size[0]}x{sheet.size[1]}, {frame_count} frames")

            agent_manifest[mode] = {
                "path": f"/assets/generated/actors/{agent_id}/sheets/{mode}-spritesheet.png?v=4",
                "frameCount": frame_count,
            }

        manifest_data[agent_id] = agent_manifest

    # Save manifest
    manifest_path = os.path.join(ACTORS_DIR, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest_data, f, indent=2)

    print("\n" + "=" * 60)
    print(f"Manifest saved to: {manifest_path}")
    print(json.dumps(manifest_data, indent=2))
    print("\n✅ All done!")

    return manifest_data


if __name__ == "__main__":
    process_all()
