# scripts/04_clip_and_stack.py

"""
This script processes pre- and post-event Sentinel-2 .SAFE folders:
    1. Clips bands to the AOI (from data/aoi/myanmar_aoi_bbox.geojson)
    2. Resamples 20m bands to 10m resolution
    3. Stacks selected bands into multiband GeoTIFFs
    4. Saves output to: data/processed/stacks/pre/ and data/processed/stacks/post/
"""

import os
import sys
import glob
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
from rasterio.mask import mask
import geopandas as gpd
from tqdm import tqdm

#Import from project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
from config.paths import PRE_EVENT_DIR, POST_EVENT_DIR, STACK_DIR, AOI_GEOJSON

# Band metadata: name -> resolution subfolder
BANDS_INFO = {
    "B02": "R10m",  # Blue
    "B03": "R10m",  # Green
    "B04": "R10m",  # Red
    "B08": "R10m",  # NIR
    "B11": "R20m",  # SWIR1
    "B12": "R20m",  # SWIR2
}

def read_and_clip_band(band_path, aoi_geom, target_shape=None, target_transform=None):
    try:
        with rasterio.open(band_path) as src:
            clipped, transform = mask(src, aoi_geom, crop=True)
            if target_shape and target_transform:
                resampled = np.empty(shape=(clipped.shape[0], *target_shape), dtype=np.float32)
                reproject(
                    source=clipped,
                    destination=resampled,
                    src_transform=transform,
                    src_crs=src.crs,
                    dst_transform=target_transform,
                    dst_crs=src.crs,
                    resampling=Resampling.bilinear,
                )
                return resampled, target_transform
            return clipped, transform
    except ValueError as e:
        if "Input shapes do not overlap raster" in str(e):
            print(f"⚠️ Skipping: {band_path.split('GRANULE')[-1].split(os.sep)[1]} — does not intersect AOI.")
            return None, None
        else:
            raise

def process_granule(granule_path, aoi_geom, output_dir, event_type):
    granule_name = os.path.basename(granule_path)
    out_path = os.path.join(output_dir, event_type, f"{granule_name}_stack.tif")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    band_arrays = []
    ref_transform = None
    ref_shape = None

    for band, res in BANDS_INFO.items():
        jp2_path = glob.glob(os.path.join(granule_path, "GRANULE", "*", "IMG_DATA", res, f"*_{band}_*.jp2"))
        if not jp2_path:
            print(f"Band {band} not found in {granule_path}")
            return

        band_array, transform = read_and_clip_band(jp2_path[0], aoi_geom)
        if band_array is None:
            return  # Skip this granule entirely

        if res == "R10m":
            ref_transform = transform
            ref_shape = band_array.shape[1:]

        band_arrays.append(band_array)

    # Resample 20m bands to 10m
    for i, (band, res) in enumerate(BANDS_INFO.items()):
        if res == "R20m":
            jp2_path = glob.glob(os.path.join(granule_path, "GRANULE", "*", "IMG_DATA", res, f"*_{band}_*.jp2"))
            if not jp2_path:
                print(f"[🚫] Band {band} not found in {granule_path}")
                return

            resampled, _ = read_and_clip_band(
                jp2_path[0],
                aoi_geom,
                target_shape=ref_shape,
                target_transform=ref_transform
            )

            if resampled is None:
                return  # Skip granule if this band doesn't intersect AOI

            band_arrays[i] = resampled

    # Stack and write
    stacked = np.concatenate(band_arrays, axis=0)
    with rasterio.open(
        out_path,
        "w",
        driver="GTiff",
        height=stacked.shape[1],
        width=stacked.shape[2],
        count=stacked.shape[0],
        dtype=stacked.dtype,
        crs="EPSG:32646",  # UTM Zone for Myanmar
        transform=ref_transform,
    ) as dst:
        for i in range(stacked.shape[0]):
            dst.write(stacked[i], i + 1)
    print(f"✅ Saved stacked image: {out_path}")

def run_all():
    aoi = gpd.read_file(AOI_GEOJSON)
    sample_jp2 = glob.glob(os.path.join(PRE_EVENT_DIR, "*", "GRANULE", "*", "IMG_DATA", "R10m", "*_B02_*.jp2"))[0]
    with rasterio.open(sample_jp2) as src:
        raster_crs = src.crs
    aoi = aoi.to_crs(raster_crs)
    aoi_geom = [feature["geometry"] for feature in aoi.__geo_interface__["features"]]

    for label, path in [("pre", PRE_EVENT_DIR), ("post", POST_EVENT_DIR)]:
        print(f"\nProcessing {label}-event granules from {path}...")
        for folder in tqdm(sorted(os.listdir(path))):
            full_path = os.path.join(path, folder)
            if os.path.isdir(full_path):
                process_granule(full_path, aoi_geom, STACK_DIR, event_type=label)

if __name__ == "__main__":
    run_all()
