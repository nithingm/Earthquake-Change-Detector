#!/usr/bin/env python3
# scripts/00_run_pipeline.py

"""
Master pipeline to run:
1. Download Sentinel-2
2. Generate AOI GeoJSON
3. Download OSM data
4. Clip & stack satellite bands
5. Compute NDVI, NDBI, NDWI (+ diff)
6. Visualize change maps
"""

import os
import subprocess

SCRIPTS = [
    "01_download_sentinel.py",
    "02_generate_aoi_geojson.py",
    "03_download_osm_data.py",
    "04_clip_and_stack.py",
    "05_compute_indices.py",
    "06_visualize_indices.py"
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def run_step(script_name):
    path = os.path.join(SCRIPT_DIR, script_name)
    print(f"\nRunning: {script_name}")
    result = subprocess.run(["python", path])
    if result.returncode != 0:
        print(f"❌ Error in {script_name}. Stopping pipeline.")
        exit(1)
    else:
        print(f"✅ Completed: {script_name}")

def main():
    print("Myanmar Earthquake 2025 — Change Detection Pipeline")
    print("Starting full pipeline...\n")

    for script in SCRIPTS:
        run_step(script)

    print("\nPipeline completed successfully!")

if __name__ == "__main__":
    main()
