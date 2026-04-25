#!/usr/bin/env python3
"""
Process AI-generated pixel art spritesheets for ClawLibrary v4.
Smart character detection: finds individual characters by content analysis.
"""

from PIL import Image
import os

BRAIN = "/home/berker/.gemini/antigravity/brain/5afb264b-9935-4d91-82a1-b4fda7280027"
ACTORS_BASE = "/home/berker/Documentos/ANTIGRAVITY/ClawLibrary-Sebas/public/assets/generated/actors"

SPRITES = {
    "kora-robot-v1": {
        "stand_front": f"{BRAIN}/kora_pixel_idle_1777077578159.png",
        "walk":        f"{BRAIN}/kora_pixel_walk_1777077634210.png",
        "work":        f"{BRAIN}/kora_pixel_work_1777077649517.png",
    },
    "sumi-secretary-v1": {
        "stand_front": f"{BRAIN}/sumi_pixel_idle_1777077588397.png",
        "walk":        f"{BRAIN}/sumi_pixel_walk_1777077664466.png",
        "work":        f"{BRAIN}/sumi_pixel_work_1777077696899.png",
    },
    "gael-doctor-v1": {
        "stand_front": f"{BRAIN}/gael_pixel_idle_1777077600973.png",
        "walk":        f"{BRAIN}/gael_pixel_walk_1777077712499.png",
        "work":        f"{BRAIN}/gael_pixel_work_1777077726711.png",
    },
}

FRAME_SIZE = 128


def remove_checkerboard(img: Image.Image, block_size: int = 16) -> Image.Image:
    """
    Remove checkerboard transparency pattern globally.
    Detects the specific alternating pattern by checking neighbors.
    Only removes pixels that are part of the alternating gray pattern.
    """
    img = img.convert("RGBA")
    pixels = img.load()
    w, h = img.size
    
    # Detect if checkerboard is present by sampling corners
    corner_colors = []
    for cx, cy in [(2,2), (w-3,2), (2,h-3), (w-3,h-3), (20,2), (2,20)]:
        if 0 <= cx < w and 0 <= cy < h:
            r, g, b, a = pixels[cx, cy]
            is_grey = abs(r - g) < 8 and abs(g - b) < 8
            # Wide range to catch both light (128/192) and dark (63/127) checkerboards
            if is_grey and (55 < r < 145 or 175 < r < 210):
                corner_colors.append(r)
    
    if len(corner_colors) < 3:
        return img  # No checkerboard detected
    
    # Determine the two checker colors from corners
    vals = sorted(set(corner_colors))
    if len(vals) < 2:
        return img
    
    # Find the two most distinct groups
    light_vals = [v for v in corner_colors if v > (min(vals) + max(vals)) / 2]
    dark_vals = [v for v in corner_colors if v <= (min(vals) + max(vals)) / 2]
    
    if not light_vals or not dark_vals:
        return img
    
    light_ref = sum(light_vals) // len(light_vals)
    dark_ref = sum(dark_vals) // len(dark_vals)
    
    # Auto-detect block size by scanning top row for transitions
    last_val = pixels[0, 0][0]
    transitions = []
    for x in range(1, min(300, w)):
        r, g, b, a = pixels[x, 0]
        is_grey = abs(r - g) < 8 and abs(g - b) < 8
        if is_grey and abs(r - last_val) > 20:
            transitions.append(x)
            last_val = r
    
    if len(transitions) >= 2:
        block = transitions[1] - transitions[0]
    else:
        block = 16  # default
    
    print(f"    ⚡ Checkerboard detected (light={light_ref}, dark={dark_ref}, block={block}px) — removing")
    
    # Mark checker pixels: must match checker color AND have alternating neighbor
    to_remove = set()
    
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if a < 128:
                continue
            
            is_grey = abs(r - g) < 8 and abs(g - b) < 8
            if not is_grey:
                continue
            
            is_light = abs(r - light_ref) < 12
            is_dark = abs(r - dark_ref) < 12
            
            if not (is_light or is_dark):
                continue
            
            # Check if neighbors at block_size distance have the OPPOSITE checker color
            has_opposite = False
            for dist in [block, block-1, block+1]:
                for dx, dy in [(-dist, 0), (dist, 0), (0, -dist), (0, dist)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h:
                        nr, ng, nb, na = pixels[nx, ny]
                        if na < 128:
                            continue
                        n_grey = abs(nr - ng) < 8 and abs(ng - nb) < 8
                        if not n_grey:
                            continue
                        if is_light and abs(nr - dark_ref) < 12:
                            has_opposite = True
                            break
                        elif is_dark and abs(nr - light_ref) < 12:
                            has_opposite = True
                            break
                if has_opposite:
                    break
            
            if has_opposite:
                to_remove.add((x, y))
    
    for x, y in to_remove:
        pixels[x, y] = (0, 0, 0, 0)
    
    print(f"    ⚡ Removed {len(to_remove)} checkerboard pixels")
    
    return img


def flood_fill_bg(img: Image.Image) -> Image.Image:
    """Remove background using flood fill from edges."""
    img = img.convert("RGBA")
    pixels = img.load()
    w, h = img.size
    
    visited = [[False]*h for _ in range(w)]
    stack = []
    
    # Seed from ALL edge pixels
    for x in range(w):
        stack.append((x, 0))
        stack.append((x, h-1))
    for y in range(h):
        stack.append((0, y))
        stack.append((w-1, y))
    
    while stack:
        x, y = stack.pop()
        if x < 0 or x >= w or y < 0 or y >= h:
            continue
        if visited[x][y]:
            continue
        visited[x][y] = True
        
        r, g, b, a = pixels[x, y]
        
        # Check if bg pixel
        is_grey = abs(r - g) < 25 and abs(g - b) < 25 and abs(r - b) < 25
        is_bg = is_grey and 60 < r < 240
        is_white = r > 225 and g > 225 and b > 225
        is_lavender = r > 210 and g > 210 and b > 220 and abs(r-g) < 15  # light lavender bg
        # Checkerboard pattern: alternating light gray (~192) and dark gray (~128) blocks
        is_checker_light = is_grey and 175 < r < 210
        is_checker_dark = is_grey and 115 < r < 145
        is_checker = is_checker_light or is_checker_dark
        
        if is_bg or is_white or is_lavender or is_checker:
            pixels[x, y] = (0, 0, 0, 0)
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                nx, ny = x+dx, y+dy
                if 0 <= nx < w and 0 <= ny < h and not visited[nx][ny]:
                    stack.append((nx, ny))
    
    return img


def clean_small_artifacts(img: Image.Image, min_cluster: int = 50) -> Image.Image:
    """Remove small isolated pixel clusters (checkerboard artifacts, noise)."""
    pixels = img.load()
    w, h = img.size
    visited = [[False]*h for _ in range(w)]
    
    clusters = []  # list of (pixel_set, bounding_box)
    
    for sy in range(h):
        for sx in range(w):
            if visited[sx][sy]:
                continue
            _, _, _, a = pixels[sx, sy]
            if a < 128:
                visited[sx][sy] = True
                continue
            
            # Flood fill to find this cluster
            cluster_pixels = []
            stack = [(sx, sy)]
            while stack:
                x, y = stack.pop()
                if x < 0 or x >= w or y < 0 or y >= h:
                    continue
                if visited[x][y]:
                    continue
                visited[x][y] = True
                _, _, _, a = pixels[x, y]
                if a < 128:
                    continue
                cluster_pixels.append((x, y))
                for dx, dy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)]:
                    nx, ny = x+dx, y+dy
                    if 0 <= nx < w and 0 <= ny < h and not visited[nx][ny]:
                        stack.append((nx, ny))
            
            if len(cluster_pixels) < min_cluster:
                # Remove this small cluster
                for px, py in cluster_pixels:
                    pixels[px, py] = (0, 0, 0, 0)
    
    return img


def find_character_regions(img: Image.Image, min_size: int = 60) -> list:
    """
    Find connected regions of non-transparent pixels.
    Returns list of bounding boxes: [(x0, y0, x1, y1), ...]
    """
    pixels = img.load()
    w, h = img.size
    visited = [[False]*h for _ in range(w)]
    regions = []
    
    for sy in range(0, h, 2):  # Sample every 2px for speed
        for sx in range(0, w, 2):
            if visited[sx][sy]:
                continue
            _, _, _, a = pixels[sx, sy]
            if a < 128:
                visited[sx][sy] = True
                continue
            
            # Found a non-transparent pixel — flood fill to find region
            min_x, max_x, min_y, max_y = sx, sx, sy, sy
            stack = [(sx, sy)]
            pixel_count = 0
            
            while stack:
                x, y = stack.pop()
                if x < 0 or x >= w or y < 0 or y >= h:
                    continue
                if visited[x][y]:
                    continue
                visited[x][y] = True
                
                _, _, _, a = pixels[x, y]
                if a < 128:
                    continue
                
                pixel_count += 1
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)
                
                for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nx, ny = x+dx, y+dy
                    if 0 <= nx < w and 0 <= ny < h and not visited[nx][ny]:
                        stack.append((nx, ny))
            
            reg_w = max_x - min_x
            reg_h = max_y - min_y
            if reg_w > min_size and reg_h > min_size and pixel_count > 100:
                regions.append((min_x, min_y, max_x + 1, max_y + 1, pixel_count))
    
    # Sort by position (top-left first, row by row)
    if regions:
        # Determine rows by y-coordinate clustering
        regions.sort(key=lambda r: (r[1], r[0]))
    
    return regions


def merge_close_regions(regions: list, merge_dist: int = 15) -> list:
    """Merge regions that are very close (likely same character with gap)."""
    if not regions:
        return []
    
    merged = [list(regions[0])]
    
    for reg in regions[1:]:
        x0, y0, x1, y1, px = reg
        found_merge = False
        
        for m in merged:
            mx0, my0, mx1, my1, mpx = m
            # Check overlap or close proximity
            if (x0 < mx1 + merge_dist and x1 > mx0 - merge_dist and
                y0 < my1 + merge_dist and y1 > my0 - merge_dist):
                m[0] = min(m[0], x0)
                m[1] = min(m[1], y0)
                m[2] = max(m[2], x1)
                m[3] = max(m[3], y1)
                m[4] += px
                found_merge = True
                break
        
        if not found_merge:
            merged.append(list(reg))
    
    return [tuple(m) for m in merged]


def extract_characters(img: Image.Image) -> list:
    """Extract individual character frames from the image."""
    regions = find_character_regions(img)
    
    # Merge very close regions
    regions = merge_close_regions(regions)
    
    # Sort: top-to-bottom, left-to-right
    if regions:
        # Group by rows (similar y values)
        regions.sort(key=lambda r: r[1])
        row_groups = []
        current_row = [regions[0]]
        
        for reg in regions[1:]:
            # Same row if y-center is within 80px
            prev_cy = (current_row[0][1] + current_row[0][3]) / 2
            curr_cy = (reg[1] + reg[3]) / 2
            if abs(curr_cy - prev_cy) < 80:
                current_row.append(reg)
            else:
                row_groups.append(sorted(current_row, key=lambda r: r[0]))
                current_row = [reg]
        row_groups.append(sorted(current_row, key=lambda r: r[0]))
        
        regions = []
        for row in row_groups:
            regions.extend(row)
    
    print(f"    Found {len(regions)} character regions")
    
    frames = []
    for i, (x0, y0, x1, y1, px) in enumerate(regions):
        frame = img.crop((x0, y0, x1, y1))
        frames.append(frame)
    
    # Limit to 6 best frames if too many detected
    if len(frames) > 9:
        # Keep only the 6 largest
        frames_with_size = [(f, f.getbbox()) for f in frames]
        frames_with_size = [(f, b) for f, b in frames_with_size if b]
        frames_with_size.sort(key=lambda x: (x[1][2]-x[1][0])*(x[1][3]-x[1][1]), reverse=True)
        frames = [f for f, _ in frames_with_size[:6]]
    
    return frames


def fit_frame(frame: Image.Image, target: int = 128) -> Image.Image:
    """Fit a character frame into target x target."""
    bbox = frame.getbbox()
    if not bbox:
        return Image.new("RGBA", (target, target), (0, 0, 0, 0))
    
    content = frame.crop(bbox)
    cw, ch = content.size
    
    # Fill 80% of target
    scale = min((target * 0.80) / cw, (target * 0.80) / ch)
    scale = min(scale, 3.0)  # Max 3x upscale
    
    new_w = max(1, int(cw * scale))
    new_h = max(1, int(ch * scale))
    
    scaled = content.resize((new_w, new_h), Image.NEAREST)
    
    canvas = Image.new("RGBA", (target, target), (0, 0, 0, 0))
    ox = (target - new_w) // 2
    oy = target - new_h - 6  # Bottom-aligned with 6px margin
    canvas.paste(scaled, (ox, oy), scaled)
    
    return canvas


def build_spritesheet(frames: list, fs: int = 128) -> tuple:
    """Build spritesheet."""
    n = len(frames)
    cols = min(n, 7)
    rows = (n + cols - 1) // cols
    
    sheet = Image.new("RGBA", (cols * fs, rows * fs), (0, 0, 0, 0))
    for i, frame in enumerate(frames):
        r = i // cols
        c = i % cols
        fitted = fit_frame(frame, fs)
        sheet.paste(fitted, (c * fs, r * fs), fitted)
    
    return sheet, n


def process_all():
    for agent_id, sprite_map in SPRITES.items():
        print(f"\n=== {agent_id} ===")
        
        for mode_name, src_path in sprite_map.items():
            print(f"  [{mode_name}]")
            
            img = Image.open(src_path).convert("RGBA")
            img = remove_checkerboard(img)
            img = flood_fill_bg(img)
            img = clean_small_artifacts(img)
            
            frames = extract_characters(img)
            
            if not frames:
                print(f"    ⚠ No frames found!")
                continue
            
            sheet, count = build_spritesheet(frames, FRAME_SIZE)
            
            out_dir = os.path.join(ACTORS_BASE, agent_id, "sheets")
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, f"{mode_name}-spritesheet.png")
            sheet.save(out_path, "PNG")
            
            print(f"    → {sheet.size}, {count} frames ✓")
    
    print("\n✅ All sprites processed!")


if __name__ == "__main__":
    process_all()
