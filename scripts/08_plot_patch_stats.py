import os
import sys
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm, LinearSegmentedColormap
import numpy as np

# 📁 Path setup
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
from config.paths import OUTPUTS_DIR

INPUT_BASE = os.path.join(PROJECT_ROOT, "data", "processed", "patch_stats")
OUTPUT_BASE = os.path.join(OUTPUTS_DIR, "patch_stats_maps")
os.makedirs(OUTPUT_BASE, exist_ok=True)

# 🎨 Custom colormaps
COLOR_MAPS = {
    "ndvi": LinearSegmentedColormap.from_list("ndvi_cmap", ["red", "white", "green"]),
    "ndbi": LinearSegmentedColormap.from_list("ndbi_cmap", ["red", "white", "gold"]),
    "ndwi": LinearSegmentedColormap.from_list("ndwi_cmap", ["red", "white", "blue"]),
}

def compute_global_range(index_type):
    input_dir = os.path.join(INPUT_BASE, index_type)
    all_vals = []

    for file in os.listdir(input_dir):
        if file.endswith(".geojson"):
            gdf = gpd.read_file(os.path.join(input_dir, file))
            vals = gdf["mean_diff"].values
            all_vals.extend(vals[np.isfinite(vals)])

    all_vals = np.array(all_vals)
    return np.min(all_vals), np.max(all_vals)

def plot_map(gdf, out_path, title, cmap, vmin, vmax):
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    norm = TwoSlopeNorm(vmin=vmin, vcenter=0, vmax=vmax)

    gdf.plot(
        column="mean_diff",
        ax=ax,
        cmap=cmap,
        legend=True,
        norm=norm,
        edgecolor="black",
        linewidth=0.1
    )
    ax.set_title(title)
    ax.axis("off")
    plt.tight_layout()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"✅ Saved: {out_path}")

def run_all():
    for idx in ["ndvi", "ndbi", "ndwi"]:
        print(f"\n📊 Index: {idx.upper()}")

        vmin, vmax = compute_global_range(idx)
        print(f"  Global range: {vmin:.3f} → {vmax:.3f}")

        cmap = COLOR_MAPS[idx]
        input_dir = os.path.join(INPUT_BASE, idx)
        output_dir = os.path.join(OUTPUT_BASE, idx)
        os.makedirs(output_dir, exist_ok=True)

        for file in os.listdir(input_dir):
            if file.endswith(".geojson"):
                path = os.path.join(input_dir, file)
                gdf = gpd.read_file(path)
                tile_id = os.path.splitext(file)[0].replace("patch_stats_", "")
                out_path = os.path.join(output_dir, f"{tile_id}.png")
                plot_map(gdf, out_path, title=f"{idx.upper()} Diff — {tile_id}", cmap=cmap, vmin=vmin, vmax=vmax)

if __name__ == "__main__":
    run_all()
