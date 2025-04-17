#!/usr/bin/env python3
# scripts/05_compute_indices.py

"""
Step 5: Compute NDVI, NDBI, NDWI for each pre/post-event stacked granule
and save the difference maps (reprojected to EPSG:4326) to:
data/satellite/processed/indices/
Saves pre/post indices in original CRS for reference.
"""

import os
import sys
import re
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.errors import RasterioIOError
from tqdm import tqdm
import warnings

# Import paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
from config.paths import STACK_DIR, INDICES_DIR

# --- Index Calculation Functions ---
# Using masked arrays internally to handle potential NoData from clipping/resampling

def compute_ndvi(stack):
    """Calculates NDVI."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning) # Ignore divide-by-zero/invalid value
        # Bands: [0]=B02, [1]=B03, [2]=B04(Red), [3]=B08(NIR), [4]=B11, [5]=B12
        red = stack[2].astype(np.float32)
        nir = stack[3].astype(np.float32)
        # Create mask for invalid pixels (NoData, or denominator = 0)
        mask = (nir + red == 0) | np.isnan(nir) | np.isnan(red) | np.isinf(nir) | np.isinf(red)
        # Calculate index using np.divide for safe division
        index = np.divide(
            (nir - red),
            (nir + red),
            out=np.full_like(red, np.nan, dtype=np.float32), # Initialize output with NaN
            where=~mask # Only calculate where not masked
        )
        index[mask] = np.nan # Ensure masked areas remain NaN
    return index

def compute_ndbi(stack):
    """Calculates NDBI."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        # Bands: [3]=B08(NIR), [4]=B11(SWIR1)
        swir1 = stack[4].astype(np.float32) # Using B11 for NDBI
        nir = stack[3].astype(np.float32)
        mask = (swir1 + nir == 0) | np.isnan(swir1) | np.isnan(nir) | np.isinf(swir1) | np.isinf(nir)
        index = np.divide(
            (swir1 - nir),
            (swir1 + nir),
            out=np.full_like(swir1, np.nan, dtype=np.float32),
            where=~mask
        )
        index[mask] = np.nan
    return index

def compute_ndwi(stack):
    """Calculates NDWI (Gao version: NIR - SWIR / NIR + SWIR) often better for water bodies."""
    # Alternative: NDWI (McFeeters: Green - NIR / Green + NIR) - more sensitive to vegetation moisture
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        # Using Gao: Bands [3]=B08(NIR), [4]=B11(SWIR1)
        nir = stack[3].astype(np.float32)
        swir1 = stack[4].astype(np.float32)
        mask = (nir + swir1 == 0) | np.isnan(nir) | np.isnan(swir1) | np.isinf(nir) | np.isinf(swir1)
        index = np.divide(
            (nir - swir1),  # Note the order for Gao's NDWI
            (nir + swir1),
            out=np.full_like(nir, np.nan, dtype=np.float32),
            where=~mask
        )
        index[mask] = np.nan
    return index

# --- Map Index Names to Functions ---
INDEX_FUNCS = {
    "ndvi": compute_ndvi,
    "ndbi": compute_ndbi,
    "ndwi": compute_ndwi  # Using Gao NDWI
}


import affine # Make sure affine is imported
from rasterio.warp import transform_bounds # Import transform_bounds

# --- Helper Function to Save Raster (REVISED) ---
def save_index(out_path, index_array, src_meta, to_4326=False):
    """Saves the index array to a GeoTIFF.

    Args:
        out_path (str): Path to save the output GeoTIFF.
        index_array (np.ndarray): The calculated index data (1 band). Should use np.nan for NoData.
        src_meta (dict): Metadata dictionary from the source rasterio dataset (pre-event stack).
        to_4326 (bool): If True, reproject the output to EPSG:4326.
                        If False, save in the source CRS.
    """
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    output_nodata = np.nan

    if to_4326:
        # --- Reproject to EPSG:4326 MANUALLY ---
        dst_crs = "EPSG:4326"
        target_resolution_deg = 0.0001 # Approximate 10m in degrees

        print(f"  Manually calculating reprojection parameters to {dst_crs} with res ~{target_resolution_deg} deg")

        try:
            with rasterio.Env(CPL_CURL_VERBOSE=False):
                 # 1. Get Source Bounds
                 src_bounds = rasterio.transform.array_bounds(
                     src_meta["height"], src_meta["width"], src_meta["transform"]
                 )

                 # 2. Calculate Target Bounds by projecting source bounds
                 dst_bounds = transform_bounds(
                     src_meta["crs"], dst_crs, *src_bounds
                 )
                 dst_left, dst_bottom, dst_right, dst_top = dst_bounds

                 print(f"    Src Bounds (UTM): {src_bounds}")
                 print(f"    Dst Bounds (WGS84): {dst_bounds}")

                 # 3. Define Target Transform MANUALLY
                 # Pixel width is positive, height is negative
                 # Top-left corner origin
                 dst_transform = affine.Affine(
                     target_resolution_deg,  # Pixel width (a)
                     0.0,                    # Rotation (b)
                     dst_left,               # Top-left X (c)
                     0.0,                    # Rotation (d)
                     -target_resolution_deg, # Pixel height (e) - negative!
                     dst_top                 # Top-left Y (f)
                 )

                 # 4. Calculate Target Dimensions based on bounds and resolution
                 dst_width = int(round((dst_right - dst_left) / target_resolution_deg))
                 dst_height = int(round((dst_top - dst_bottom) / target_resolution_deg))

                 print(f"    --> Manually Calculated Dst Transform: {dst_transform}")
                 print(f"    --> Manually Calculated Dst W/H: {dst_width}/{dst_height}")

                 if dst_width <= 0 or dst_height <= 0:
                      print(f"  🚨 FATAL WARNING: Calculated zero or negative dimensions ({dst_width}x{dst_height}). Cannot proceed.")
                      return # Stop processing this file

                 # --- Prepare Output Metadata ---
                 profile = src_meta.copy()
                 profile.update({
                     "crs": dst_crs,
                     "transform": dst_transform, # Use the MANUALLY calculated transform
                     "width": dst_width,         # Use the MANUALLY calculated width
                     "height": dst_height,       # Use the MANUALLY calculated height
                     "count": 1,
                     "dtype": "float32",
                     "nodata": output_nodata,
                     "driver": "GTiff"
                 })
                 for key in ['blockxsize', 'blockysize', 'tiled', 'compress', 'interleave']:
                     profile.pop(key, None)

                 # --- Perform Reprojection ---
                 destination = np.empty((dst_height, dst_width), dtype=np.float32)
                 destination.fill(output_nodata)

                 reproject(
                     source=index_array,
                     destination=destination,
                     src_transform=src_meta['transform'],
                     src_crs=src_meta['crs'],
                     src_nodata=np.nan,
                     dst_transform=dst_transform, # Use manual transform
                     dst_crs=dst_crs,
                     dst_nodata=output_nodata,
                     dst_width=dst_width,     # Explicitly provide dimensions
                     dst_height=dst_height,   # Explicitly provide dimensions
                     resampling=Resampling.bilinear
                 )

                 # --- Write Output ---
                 print(f"  Writing reprojected file: {out_path}")
                 with rasterio.open(out_path, 'w', **profile) as dst:
                     dst.write(destination, 1)

                 # --- Verification Step (with corrected logic) ---
                 print(f"  Verifying saved file: {os.path.basename(out_path)}")
                 with rasterio.open(out_path) as verify_src:
                     print(f"    VERIFY CRS: {verify_src.crs}")
                     print(f"    VERIFY Transform: {verify_src.transform}")

                     # --- CORRECTED Verification Check ---
                     pixel_width_ok = abs(verify_src.transform.a) > 1e-9
                     pixel_height_ok = abs(verify_src.transform.e) > 1e-9
                     if pixel_width_ok and pixel_height_ok:
                         print("    ✅ Transform pixel size looks valid (non-zero).")
                     else:
                         print("    🚨 WARNING: Transform pixel size is zero or near-zero!")
                         if not pixel_width_ok: print(f"       Pixel width (a): {verify_src.transform.a}")
                         if not pixel_height_ok: print(f"       Pixel height (e): {verify_src.transform.e}")
                     # --- End Corrected Check ---

                     print(f"    VERIFY Bounds: {verify_src.bounds}")
                     print(f"    VERIFY Shape: {verify_src.shape}")
                     print(f"    VERIFY NoData: {verify_src.nodata}")

        except Exception as e:
             print(f"❌ ERROR during manual reprojection/saving for {out_path}: {e}")
             import traceback
             traceback.print_exc()

    else:
        # --- Save in original CRS (Keep the same as previous version) ---
        profile = src_meta.copy()
        profile.update({
            "count": 1, "dtype": "float32", "nodata": output_nodata, "driver": "GTiff"
        })
        for key in ['blockxsize', 'blockysize', 'tiled', 'compress', 'interleave']:
            profile.pop(key, None)

        print(f"  Writing original CRS file: {out_path}")
        try:
            with rasterio.open(out_path, "w", **profile) as dst:
                dst.write(index_array.astype(np.float32), 1)
            print(f"    Successfully wrote {os.path.basename(out_path)}")
        except Exception as e:
             print(f"❌ ERROR writing original CRS file {out_path}: {e}")
             import traceback
             traceback.print_exc()

# --- Function to Compute Index for a Stack ---
def compute_and_save_index(func, stack_path, out_path, to_4326=False):
    """Computes index for a given stack file and saves it."""
    if not os.path.exists(stack_path):
        print(f"  ❌ ERROR: Input stack file not found: {stack_path}")
        return False # Indicate failure

    try:
        print(f"  Processing stack: {os.path.basename(stack_path)}")
        with rasterio.open(stack_path) as src:
            # Read metadata first
            meta = src.meta.copy()
            print(f"    Input stack CRS: {meta['crs']}, Shape: ({meta['count']}, {meta['height']}, {meta['width']})")

            # Check if stack has expected number of bands (at least 6 for B12)
            if meta['count'] < 6:
                 print(f"    ❌ ERROR: Input stack {os.path.basename(stack_path)} has only {meta['count']} bands. Expected 6.")
                 return False

            # Read data as float32, respecting NoData if set in metadata
            stack_data = src.read(masked=True).astype(np.float32)
            # Fill NoData areas (represented by mask) with NaN before calculation
            stack_data = stack_data.filled(np.nan)

        # Compute the index using the appropriate function
        print(f"    Calculating index...")
        index_array = func(stack_data) # Function should return array with NaN for NoData

        # Save the result
        save_index(out_path, index_array, meta, to_4326=to_4326)
        return True # Indicate success

    except RasterioIOError as e:
        print(f"  ❌ ERROR opening/reading stack file {os.path.basename(stack_path)}: {e}")
        return False
    except Exception as e:
        print(f"  ❌ UNEXPECTED ERROR processing {os.path.basename(stack_path)}: {e}")
        import traceback
        traceback.print_exc()
        return False

# --- Function to Extract Tile ID ---
def get_tile_id(filename):
    """Extracts the Sentinel-2 tile ID (e.g., T47QKD) from a filename."""
    # Match T + 2 digits + 3 letters
    match = re.search(r"(T\d{2}[A-Z]{3})", filename)
    return match.group(1) if match else None


# --- Main Processing Logic ---
def run_all():
    pre_dir = os.path.join(STACK_DIR, "pre")
    post_dir = os.path.join(STACK_DIR, "post")
    os.makedirs(INDICES_DIR, exist_ok=True)

    # Check if stack directories exist
    if not os.path.isdir(pre_dir):
        print(f"❌ ERROR: Pre-event stack directory not found: {pre_dir}")
        sys.exit(1) # Exit if essential input is missing
    if not os.path.isdir(post_dir):
        print(f"❌ ERROR: Post-event stack directory not found: {post_dir}")
        sys.exit(1)

    # Find stack files and extract tile IDs
    try:
        pre_files = sorted([os.path.join(pre_dir, f) for f in os.listdir(pre_dir) if f.endswith("_stack.tif")])
        post_files = sorted([os.path.join(post_dir, f) for f in os.listdir(post_dir) if f.endswith("_stack.tif")])
    except OSError as e:
        print(f"❌ ERROR listing files in stack directories: {e}")
        sys.exit(1)

    # Create dictionary mapping tile ID to full path
    pre_tiles = {tile_id: f for f in pre_files if (tile_id := get_tile_id(f))}
    post_tiles = {tile_id: f for f in post_files if (tile_id := get_tile_id(f))}

    # Find common tile IDs
    common_tiles = sorted(list(set(pre_tiles.keys()) & set(post_tiles.keys())))

    if not common_tiles:
        print("❌ No common tiles found between pre and post stack directories.")
        print(f"  Pre tiles found: {list(pre_tiles.keys())}")
        print(f"  Post tiles found: {list(post_tiles.keys())}")
        sys.exit(1) # Exit if no work can be done

    print(f"Found {len(common_tiles)} common tiles: {common_tiles}")
    print("\n--- Verifying Input Stack Metadata (Example) ---")
    if common_tiles: # Check if we have common tiles to test
        example_tile_id = common_tiles[0] # Get the first common tile ID
        if example_tile_id in pre_tiles: # Ensure it exists in pre_tiles dict
            example_stack_path = pre_tiles[example_tile_id]
            if os.path.exists(example_stack_path):
                try:
                    print(f"Attempting to open: {example_stack_path}")
                    with rasterio.open(example_stack_path) as src:
                        print(f"Successfully opened: {os.path.basename(example_stack_path)}")
                        print(f"  CRS: {src.crs}")
                        print(f"  Transform: {src.transform}")
                        print(f"  Bounds: {src.bounds}")
                        print(f"  Resolution (X, Y): {src.res}")
                        print(f"  Width: {src.width}, Height: {src.height}")
                        print(f"  NoData: {src.nodata}") # Check if NoData is set

                        # --- Stricter Checks ---
                        is_crs_correct = src.crs == rasterio.crs.CRS.from_epsg(32646)
                        print(f"  Is CRS EPSG:32646? : {is_crs_correct}")
                        if not is_crs_correct:
                            print(f"  🚨 FATAL WARNING: Input stack CRS is NOT EPSG:32646! It is {src.crs}.")

                        # Check if pixel size is reasonably close to 10m (allow small tolerance)
                        is_res_correct = abs(src.res[0] - 10.0) < 0.1 and abs(src.res[1] - 10.0) < 0.1
                        print(f"  Is Resolution ~10m? : {is_res_correct}")
                        if not is_res_correct:
                            print(f"  🚨 FATAL WARNING: Input stack pixel size is NOT ~10m! Resolution: {src.res}")

                        # Check if transform elements look valid (non-zero pixel size)
                        is_transform_valid = abs(src.transform.a) > 1e-6 and abs(src.transform.e) > 1e-6
                        print(f"  Is Transform valid (non-zero pixel size)? : {is_transform_valid}")
                        if not is_transform_valid:
                            print(f"  🚨 FATAL WARNING: Input stack transform has zero or near-zero pixel size!")

                except Exception as e:
                    print(f"  ❌ ERROR opening/reading example stack {example_stack_path}: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"  Example stack file not found: {example_stack_path}")
        else:
            print(f"Could not find example tile {example_tile_id} in pre_tiles dictionary.")
    else:
        print("  Cannot verify input stack, no common_tiles found.")
    print("-------------------------------------------------\n")
    # --- Loop through each index type (NDVI, NDBI, NDWI) ---
    for index_name, index_func in INDEX_FUNCS.items():
        print(f"\n📊 Computing {index_name.upper()} for {len(common_tiles)} common tiles...")

        # Create output directories for the current index
        idx_base_dir = os.path.join(INDICES_DIR, index_name)
        idx_pre_dir = os.path.join(idx_base_dir, "pre")
        idx_post_dir = os.path.join(idx_base_dir, "post")
        idx_diff_dir = os.path.join(idx_base_dir, "diff")
        os.makedirs(idx_pre_dir, exist_ok=True)
        os.makedirs(idx_post_dir, exist_ok=True)
        os.makedirs(idx_diff_dir, exist_ok=True)

        # --- Loop through each common tile ID ---
        for tile_id in tqdm(common_tiles, desc=f"[{index_name.upper()}] Tiles"):
            print(f"\n--- Processing Tile: {tile_id} for {index_name.upper()} ---")
            pre_stack_path = pre_tiles[tile_id]
            post_stack_path = post_tiles[tile_id]

            # Define output paths for this tile and index
            out_pre_path = os.path.join(idx_pre_dir, f"{tile_id}.tif")
            out_post_path = os.path.join(idx_post_dir, f"{tile_id}.tif")
            out_diff_path = os.path.join(idx_diff_dir, f"{tile_id}_diff.tif")

            # --- Compute and save pre/post indices (in original CRS) ---
            print(f"-> Computing PRE index for {tile_id}")
            pre_success = compute_and_save_index(index_func, pre_stack_path, out_pre_path, to_4326=False)

            print(f"-> Computing POST index for {tile_id}")
            post_success = compute_and_save_index(index_func, post_stack_path, out_post_path, to_4326=False)

            # --- Compute and save difference map (reprojected to EPSG:4326) ---
            if pre_success and post_success:
                print(f"-> Computing DIFF index for {tile_id} (reprojecting to EPSG:4326)")
                try:
                    # Open the just-created pre/post index files
                    with rasterio.open(out_pre_path) as src_pre, \
                         rasterio.open(out_post_path) as src_post:

                        # Double-check CRS and shape match before calculating difference
                        if src_pre.crs != src_post.crs:
                            print(f"  ❌ ERROR: CRS mismatch between pre ({src_pre.crs}) and post ({src_post.crs}) for tile {tile_id}. Cannot calculate difference.")
                            continue # Skip to next tile
                        if src_pre.shape != src_post.shape:
                             print(f"  ❌ ERROR: Shape mismatch between pre ({src_pre.shape}) and post ({src_post.shape}) for tile {tile_id}. Cannot calculate difference.")
                             continue

                        # Get metadata from pre-event index (to use as base for diff's reprojection)
                        meta_pre = src_pre.meta.copy()

                        # Read index data, treating NoData as NaN
                        pre_idx = src_pre.read(1, masked=True).filled(np.nan)
                        post_idx = src_post.read(1, masked=True).filled(np.nan)

                        # Calculate difference (Post - Pre)
                        diff = post_idx - pre_idx # NaN propagation happens automatically

                    # Save the difference map, reprojecting to EPSG:4326 using pre-event meta
                    save_index(out_diff_path, diff, meta_pre, to_4326=True)
                    print(f"[✓] {index_name.upper()} difference calculation complete for tile: {tile_id}")

                except RasterioIOError as e:
                    print(f"  ❌ ERROR opening pre/post index files for difference calculation ({tile_id}): {e}")
                except Exception as e:
                    print(f"  ❌ UNEXPECTED ERROR calculating difference for tile {tile_id}: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"  ⚠️ Skipping DIFF calculation for {tile_id} due to errors in PRE/POST index generation.")

        print(f"\n✅ Finished computing {index_name.upper()}.")

    print("\nAll index computations complete.")

# --- Run the Script ---
if __name__ == "__main__":
    run_all()