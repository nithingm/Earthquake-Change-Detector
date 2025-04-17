import os
import re
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib import colormaps
import rasterio

def extract_tile_id(filename):
    match = re.search(r"_T(\d{2}[A-Z]{3})_", filename)
    return f"T{match.group(1)}" if match else None

def load_band(path):
    with rasterio.open(path) as src:
        return src.read(1)

def save_visual(img, title, cmap, out_path, vmin=-1, vmax=1):
    plt.figure(figsize=(10, 8))
    plt.imshow(img, cmap=cmap, vmin=vmin, vmax=vmax)
    plt.colorbar(label=title)
    plt.title(title)
    plt.axis("off")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()
