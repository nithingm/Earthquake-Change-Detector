# scripts/05_compute_indices.py

"""
Step 5: Compute NDVI, NDBI, NDWI for each pre/post-event stacked granule
and save the difference maps to: data/satellite/processed/indices/
"""

import os
import sys
import re
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from tqdm import tqdm

# Import paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
from config.paths import STACK_DIR, INDICES_DIR

# Define index formulas based on band order: [0]=B02, [1]=B03, [2]=B04, [3]=B08, [4]=B11, [5]=B12
def compute_ndvi(stack):
    red = stack[2].astype(float)
    nir = stack[3].astype(float)
    with np.errstate(divide='ignore', invalid='ignore'):
        index = (nir - red) / (nir + red)
        index[np.isnan(index)] = 0
    return index

def compute_ndbi(stack):
    swir = stack[4].astype(float)
    nir = stack[3].astype(float)
    with np.errstate(divide='ignore', invalid='ignore'):
        index = (swir - nir) / (swir + nir)
        index[np.isnan(index)] = 0
    return index

def compute_ndwi(stack):
    green = stack[1].astype(float)
    nir = stack[3].astype(float)
    with np.errstate(divide='ignore', invalid='ignore'):
        index = (green - nir) / (green + nir)
        index[np.isnan(index)] = 0
    return index

INDEX_FUNCS = {
    "ndvi": compute_ndvi,
    "ndbi": compute_ndbi,
    "ndwi": compute_ndwi
}

def save_index(out_path, index_array, ref_meta, to_4326=False):
    meta = ref_meta.copy()
    meta.update({"count": 1, "dtype": "float32"})

    if to_4326:
        dst_crs = "EPSG:4326"
        transform, width, height = calculate_default_transform(
            ref_meta["crs"], dst_crs, ref_meta["width"], ref_meta["height"], *ref_meta["transform"][:6]
        )
        dst_array = np.empty((height, width), dtype=np.float32)
        new_meta = meta.copy()
        new_meta.update({
            "crs": dst_crs,
            "transform": transform,
            "width": width,
            "height": height
        })
        reproject(
            source=index_array,
            destination=dst_array,
            src_transform=ref_meta["transform"],
            src_crs=ref_meta["crs"],
            dst_transform=transform,
            dst_crs=dst_crs,
            resampling=Resampling.bilinear
        )
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with rasterio.open(out_path, "w", **new_meta) as dst:
            dst.write(dst_array, 1)
    else:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with rasterio.open(out_path, "w", **meta) as dst:
            dst.write(index_array.astype("float32"), 1)

def compute_and_save_index(func, stack_path, out_path, to_4326=False):
    with rasterio.open(stack_path) as src:
        stack = src.read()
        meta = src.meta
    index_array = func(stack)
    save_index(out_path, index_array, meta, to_4326=to_4326)

def get_tile_id(filename):
    match = re.search(r"T\d{2}[A-Z]{3}", filename)
    return match.group() if match else None

def run_all():
    pre_dir = os.path.join(STACK_DIR, "pre")
    post_dir = os.path.join(STACK_DIR, "post")
    os.makedirs(INDICES_DIR, exist_ok=True)

    pre_files = sorted(f for f in os.listdir(pre_dir) if f.endswith(".tif"))
    post_files = sorted(f for f in os.listdir(post_dir) if f.endswith(".tif"))

    pre_tiles = {get_tile_id(f): f for f in pre_files}
    post_tiles = {get_tile_id(f): f for f in post_files}
    common_tiles = sorted(set(pre_tiles.keys()) & set(post_tiles.keys()))

    for index_name, func in INDEX_FUNCS.items():
        print(f"\n📊 Computing {index_name.upper()} for {len(common_tiles)} tiles...")
        for tile_id in tqdm(common_tiles):
            pre_stack = os.path.join(pre_dir, pre_tiles[tile_id])
            post_stack = os.path.join(post_dir, post_tiles[tile_id])

            out_pre = os.path.join(INDICES_DIR, index_name, "pre", f"{tile_id}.tif")
            out_post = os.path.join(INDICES_DIR, index_name, "post", f"{tile_id}.tif")
            out_diff = os.path.join(INDICES_DIR, index_name, "diff", f"{tile_id}_diff.tif")

            compute_and_save_index(func, pre_stack, out_pre)
            compute_and_save_index(func, post_stack, out_post)

            with rasterio.open(out_pre) as src_pre, rasterio.open(out_post) as src_post:
                diff = src_post.read(1) - src_pre.read(1)
                meta = src_pre.meta
                save_index(out_diff, diff, meta, to_4326=True)

            print(f"[✓] {index_name.upper()} done for tile: {tile_id}")

if __name__ == "__main__":
    run_all()
