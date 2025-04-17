# scripts/06_visualize_indices.py

"""
Step 6: Visualize NDVI, NDBI, NDWI index rasters and their differences
Saves visuals to: outputs/visuals/<index>/<pre|post|diff>/*.png
"""

import os
import sys
import re
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colormaps

# Import paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
from config.paths import INDICES_DIR, VISUALS_DIR

INDEX_TYPES = ["ndvi", "ndbi", "ndwi"]

#Extract tile ID (e.g., T47QME) from filename
def extract_tile_id(filename):
    match = re.search(r"T\d{2}[A-Z]{3}", filename)
    return match.group() if match else None

#Load 1-band raster
def load_raster(path):
    with rasterio.open(path) as src:
        return src.read(1)

#Plot and save
def save_plot(array, title, cmap, out_path, vmin=-1, vmax=1):
    plt.figure(figsize=(10, 8))
    plt.imshow(array, cmap=cmap, vmin=vmin, vmax=vmax)
    plt.colorbar(label=title)
    plt.title(title)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()

def visualize_index(index):
    print(f"\nVisualizing {index.upper()}...")
    base_dir = os.path.join(INDICES_DIR, index)
    pre_dir = os.path.join(base_dir, "pre")
    post_dir = os.path.join(base_dir, "post")
    diff_dir = os.path.join(base_dir, "diff")

    os.makedirs(os.path.join(VISUALS_DIR, index, "pre"), exist_ok=True)
    os.makedirs(os.path.join(VISUALS_DIR, index, "post"), exist_ok=True)
    os.makedirs(os.path.join(VISUALS_DIR, index, "diff"), exist_ok=True)

    tile_ids = set(
        extract_tile_id(f) for f in os.listdir(diff_dir) if f.endswith(".tif")
    )

    cmap_base = {
        "ndvi": "RdYlGn",
        "ndbi": "Greys",
        "ndwi": "YlGnBu"
    }.get(index, "viridis")
    cmap_diff = colormaps["bwr"]

    for tile_id in tile_ids:
        f_pre = os.path.join(pre_dir, f"{tile_id}.tif")
        f_post = os.path.join(post_dir, f"{tile_id}.tif")
        f_diff = os.path.join(diff_dir, f"{tile_id}_diff.tif")

        if not (os.path.exists(f_pre) and os.path.exists(f_post) and os.path.exists(f_diff)):
            print(f"⚠️ Skipping {tile_id} — some files missing.")
            continue

        img_pre = load_raster(f_pre)
        img_post = load_raster(f_post)
        img_diff = load_raster(f_diff)

        save_plot(img_pre, f"{index.upper()} - Pre ({tile_id})", cmap_base, os.path.join(VISUALS_DIR, index, "pre", f"{tile_id}.png"))
        save_plot(img_post, f"{index.upper()} - Post ({tile_id})", cmap_base, os.path.join(VISUALS_DIR, index, "post", f"{tile_id}.png"))
        save_plot(img_diff, f"{index.upper()} Difference ({tile_id})", cmap_diff, os.path.join(VISUALS_DIR, index, "diff", f"{tile_id}_diff.png"))

        print(f"[✓] Saved {index.upper()} visualizations for tile: {tile_id}")

def run_all():
    for index in INDEX_TYPES:
        visualize_index(index)

if __name__ == "__main__":
    run_all()
