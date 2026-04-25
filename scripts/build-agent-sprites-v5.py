#!/usr/bin/env python3
"""
build-agent-sprites-v5.py  –  Chroma-key sprite pipeline
=========================================================
Procesa imágenes con fondo verde (#00FF00) para generar spritesheets
limpios con transparencia real para Phaser 3.

Workflow:
1. Lee imagen fuente (4 poses en cuadrícula 2x2)
2. Elimina el verde chroma-key → canal alfa
3. Detecta los 4 personajes por bounding-box
4. Normaliza cada frame a 128x128px
5. Genera spritesheet horizontal (6 frames: ping-pong)
"""

import os
import sys
from PIL import Image
import json
from pathlib import Path

# ──────────────────────────────────────────────
# CONFIGURACIÓN
# ──────────────────────────────────────────────

FRAME_SIZE = 128  # px por frame final
GREEN_THRESHOLD = 80  # Tolerancia para chroma-key

# Mapeo de imágenes fuente → destino
# Las imágenes se buscan en el directorio "sources"
AGENTS = {
    "kora-robot-v1": {
        "idle": "kora_idle_greenscreen",
        "walk": "kora_walk_greenscreen",
        "work": "kora_work_greenscreen",
    },
    "sumi-secretary-v1": {
        "idle": "sumi_idle_greenscreen",
        "walk": "sumi_walk_greenscreen",
        "work": "sumi_work_greenscreen",
    },
    "gael-doctor-v1": {
        "idle": "gael_idle_greenscreen",
        "walk": "gael_walk_greenscreen",
        "work": "gael_work_greenscreen",
    },
}

# Mapeo de modo → nombre de archivo de salida
MODE_TO_FILENAME = {
    "idle": "stand_front-spritesheet.png",
    "walk": "walk_front-spritesheet.png",
    "work": "work_front-spritesheet.png",
}


def is_green_pixel(r, g, b, threshold=GREEN_THRESHOLD):
    """Determina si un pixel es fondo verde chroma-key."""
    return g > 150 and g > r + threshold and g > b + threshold


def remove_green_background(img):
    """Elimina fondo verde chroma-key y devuelve imagen RGBA."""
    img = img.convert("RGB")
    w, h = img.size
    rgba = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    src_px = img.load()
    dst_px = rgba.load()
    
    for y in range(h):
        for x in range(w):
            r, g, b = src_px[x, y]
            if is_green_pixel(r, g, b):
                dst_px[x, y] = (0, 0, 0, 0)  # Transparente
            else:
                dst_px[x, y] = (r, g, b, 255)  # Opaco
    
    return rgba


def find_character_regions(rgba_img, min_size=30):
    """
    Encuentra regiones con contenido (no-transparente) usando
    escaneo de columnas/filas para detectar los 4 cuadrantes.
    """
    w, h = rgba_img.size
    px = rgba_img.load()
    
    # Estrategia: dividir en cuadrícula 2x2 y encontrar el bounding box
    # del contenido en cada cuadrante
    half_w = w // 2
    half_h = h // 2
    
    quadrants = [
        (0, 0, half_w, half_h),           # Top-left
        (half_w, 0, w, half_h),            # Top-right
        (0, half_h, half_w, h),            # Bottom-left
        (half_w, half_h, w, h),            # Bottom-right
    ]
    
    regions = []
    for (qx1, qy1, qx2, qy2) in quadrants:
        # Encontrar bounding box del contenido no-transparente
        min_x, min_y = qx2, qy2
        max_x, max_y = qx1, qy1
        has_content = False
        
        for y in range(qy1, qy2):
            for x in range(qx1, qx2):
                if px[x, y][3] > 128:  # No transparente
                    has_content = True
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)
        
        if has_content and (max_x - min_x) >= min_size and (max_y - min_y) >= min_size:
            regions.append((min_x, min_y, max_x + 1, max_y + 1))
    
    return regions


def crop_and_normalize(rgba_img, bbox, target_size=FRAME_SIZE):
    """
    Recorta una región y la normaliza a target_size x target_size,
    centrando el personaje y manteniendo proporciones.
    """
    cropped = rgba_img.crop(bbox)
    cw, ch = cropped.size
    
    # Calcular escala para que quepa en target_size manteniendo proporción
    scale = min(target_size / cw, target_size / ch) * 0.85  # 85% para margen
    new_w = max(1, int(cw * scale))
    new_h = max(1, int(ch * scale))
    
    # Usar NEAREST para pixel art si es pequeño, LANCZOS si es grande
    resample = Image.NEAREST if scale >= 0.5 else Image.LANCZOS
    resized = cropped.resize((new_w, new_h), resample)
    
    # Centrar en canvas de target_size x target_size
    canvas = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))
    paste_x = (target_size - new_w) // 2
    paste_y = target_size - new_h - int(target_size * 0.05)  # Alinear abajo con margen
    canvas.paste(resized, (paste_x, paste_y), resized)
    
    return canvas


def build_spritesheet(frames, ping_pong=True):
    """
    Construye un spritesheet horizontal a partir de una lista de frames.
    Con ping-pong: [0,1,2,3] → [0,1,2,3,2,1] = 6 frames
    """
    if ping_pong and len(frames) >= 3:
        # Ping-pong: ida y vuelta sin repetir extremos
        full_seq = list(frames) + list(reversed(frames[1:-1]))
    else:
        full_seq = list(frames)
    
    n = len(full_seq)
    sheet_w = FRAME_SIZE * n
    sheet_h = FRAME_SIZE
    sheet = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))
    
    for i, frame in enumerate(full_seq):
        sheet.paste(frame, (i * FRAME_SIZE, 0), frame)
    
    return sheet, n


def find_source_image(source_dir, prefix):
    """Busca la imagen fuente más reciente que coincida con el prefijo."""
    candidates = []
    for f in os.listdir(source_dir):
        if f.startswith(prefix) and f.endswith(".png"):
            full = os.path.join(source_dir, f)
            candidates.append((os.path.getmtime(full), full))
    
    if not candidates:
        return None
    
    candidates.sort(reverse=True)  # Más reciente primero
    return candidates[0][1]


def process_agent(agent_id, modes, source_dir, output_base):
    """Procesa todos los modos de un agente."""
    output_dir = os.path.join(output_base, agent_id, "sheets")
    os.makedirs(output_dir, exist_ok=True)
    
    results = {}
    
    for mode, prefix in modes.items():
        src_path = find_source_image(source_dir, prefix)
        if not src_path:
            print(f"  ⚠️  No encontrada imagen para {agent_id}/{mode} (prefijo: {prefix})")
            continue
        
        print(f"  📄 {mode}: {os.path.basename(src_path)}")
        
        # 1. Cargar y eliminar fondo verde
        img = Image.open(src_path)
        print(f"     Tamaño: {img.size}, Modo: {img.mode}")
        rgba = remove_green_background(img)
        
        # 2. Detectar regiones de personajes
        regions = find_character_regions(rgba)
        print(f"     Regiones detectadas: {len(regions)}")
        
        if len(regions) < 2:
            print(f"     ⚠️  Muy pocas regiones, usando cuadrantes directos")
            w, h = rgba.size
            hw, hh = w // 2, h // 2
            regions = [
                (0, 0, hw, hh),
                (hw, 0, w, hh),
                (0, hh, hw, h),
                (hw, hh, w, h),
            ]
        
        # 3. Normalizar frames
        frames = []
        for i, bbox in enumerate(regions[:4]):
            frame = crop_and_normalize(rgba, bbox)
            frames.append(frame)
            print(f"     Frame {i}: bbox={bbox}")
        
        # 4. Construir spritesheet
        sheet, n_frames = build_spritesheet(frames)
        
        # 5. Guardar
        out_path = os.path.join(output_dir, MODE_TO_FILENAME[mode])
        sheet.save(out_path, "PNG")
        print(f"     ✅ Guardado: {out_path} ({n_frames} frames, {sheet.size[0]}x{sheet.size[1]})")
        
        results[mode] = {
            "path": out_path,
            "frameCount": n_frames,
            "frameWidth": FRAME_SIZE,
            "frameHeight": FRAME_SIZE,
        }
    
    return results


def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Directorio de imágenes fuente (generadas por IA)
    source_dir = os.path.expanduser(
        "~/.gemini/antigravity/brain/5afb264b-9935-4d91-82a1-b4fda7280027"
    )
    
    # Directorio de salida
    output_base = os.path.join(project_root, "public", "assets", "generated", "actors")
    
    print("=" * 60)
    print("🎨 Build Agent Sprites v5 — Chroma Key Pipeline")
    print("=" * 60)
    print(f"Fuentes: {source_dir}")
    print(f"Salida:  {output_base}")
    print()
    
    all_results = {}
    
    for agent_id, modes in AGENTS.items():
        print(f"\n🤖 Procesando: {agent_id}")
        print("-" * 40)
        results = process_agent(agent_id, modes, source_dir, output_base)
        all_results[agent_id] = results
    
    # Guardar manifest
    manifest_path = os.path.join(output_base, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n{'=' * 60}")
    print(f"✅ Pipeline completado. Manifest: {manifest_path}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
