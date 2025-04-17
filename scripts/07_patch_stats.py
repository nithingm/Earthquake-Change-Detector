# scripts/07_patch_stats.py

"""
Step 7: Patch-wise summary statistics from difference maps
- Input: NDVI/NDBI/NDWI difference maps (Txx_diff.tif in EPSG:4326)
- Output: GeoJSON and CSV of per-patch mean values (EPSG:4326)
"""

import os
import sys
import rasterio
import numpy as np
import geopandas as gpd
from shapely.geometry import box
import pandas as pd
from tqdm import tqdm

# 🔧 Import paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
from config.paths import INDICES_DIR

PATCH_SIZE = 128

def patch_stats(raster_path, out_dir):
    name = os.path.splitext(os.path.basename(raster_path))[0]
    out_geojson = os.path.join(out_dir, f"patch_stats_{name}.geojson")
    out_csv = os.path.join(out_dir, f"patch_stats_{name}.csv")

    try: # Add try-except for better error handling during file processing
        with rasterio.open(raster_path) as src:
            # --- Verification Step ---
            print(f"Processing {name}: Input CRS is {src.crs}")
            if src.crs != rasterio.crs.CRS.from_epsg(4326):
                print(f"⚠️ WARNING: Input raster {raster_path} is not EPSG:4326! CRS is {src.crs}. Check script 05.")
                # Decide if you want to stop or try to continue
                # return # Option: stop processing this file

            img = src.read(1, masked=True) # Use masked=True to handle NoData
            transform = src.transform
            rows, cols = img.shape

            records = []
            for row in range(0, rows, PATCH_SIZE):
                for col in range(0, cols, PATCH_SIZE):
                    # Define the window
                    window_slice = (slice(row, min(row + PATCH_SIZE, rows)), slice(col, min(col + PATCH_SIZE, cols)))
                    window_data = img[window_slice]

                    # Skip if window is empty or all NoData
                    if window_data.mask.all() or window_data.size == 0:
                        continue

                    mean_val = np.nanmean(window_data.filled(np.nan)) # Use nanmean on filled array

                    if np.isnan(mean_val): # Skip if mean is NaN (e.g., all NoData after fill)
                        continue

                    # Calculate geographic bounds using the transform
                    # transform * (pixel_x, pixel_y) -> (geo_x, geo_y) or (lon, lat)
                    minx, maxy = transform * (col, row)
                    maxx, miny = transform * (col + PATCH_SIZE, row + PATCH_SIZE) # Check corners carefully

                    # Ensure bounds are reasonable lat/lon
                    if not (-180 <= minx <= 180 and -180 <= maxx <= 180 and -90 <= miny <= 90 and -90 <= maxy <= 90):
                        print(f"  --> Skipping patch at ({row},{col}) due to bounds outside WGS84: ({minx:.2f}, {miny:.2f}, {maxx:.2f}, {maxy:.2f})")
                        continue

                    geom = box(minx, miny, maxx, maxy)
                    records.append({
                        "tile": name,
                        "row": row,
                        "col": col,
                        "mean_diff": mean_val,
                        "geometry": geom
                    })

        if not records:
            print(f"⚠️ No valid patches found for {name}")
            return

        # Create GeoDataFrame, ASSUMING input CRS was correct (EPSG:4326)
        gdf = gpd.GeoDataFrame(records, crs="EPSG:4326") # Directly assign EPSG:4326

        # --- REMOVED REDUNDANT REPROJECTION ---
        # gdf = gdf.to_crs(epsg=4326) # This line is removed/commented

        os.makedirs(out_dir, exist_ok=True)
        # Save GeoJSON (inherently EPSG:4326)
        gdf.to_file(out_geojson, driver="GeoJSON")
        # Save CSV
        gdf.drop(columns="geometry").to_csv(out_csv, index=False)
        print(f"✅ Saved: {out_geojson} ({len(records)} patches)")
        # print(f"   CSV: {out_csv}") # Less verbose output

    except Exception as e:
        print(f"❌ Error processing {raster_path}: {e}")
        import traceback
        traceback.print_exc()


def run_all():
    base_input = INDICES_DIR
    base_output = os.path.join(PROJECT_ROOT, "data", "processed", "patch_stats")

    for idx in ["ndvi", "ndbi", "ndwi"]:
        print(f"\n🔍 Running patch stats for: {idx.upper()}")
        input_dir = os.path.join(base_input, idx, "diff")
        output_dir = os.path.join(base_output, idx)
        os.makedirs(output_dir, exist_ok=True)

        if not os.path.isdir(input_dir):
            print(f"⚠️ Input directory not found, skipping: {input_dir}")
            continue

        tifs = sorted([
            os.path.join(input_dir, f) for f in os.listdir(input_dir)
            if f.endswith("_diff.tif") and f.startswith("T")
        ])

        if not tifs:
            print(f"  No difference TIFF files found in {input_dir}")
            continue

        for tif in tqdm(tifs, desc=f"[{idx.upper()}] Processing"):
            patch_stats(tif, output_dir)

if __name__ == "__main__":
    run_all()