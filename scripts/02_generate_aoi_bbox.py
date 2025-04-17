# scripts/02_generate_aoi_bbox.py

import os
import sys

# Ensure config import works
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

import geopandas as gpd
from shapely.geometry import box
from config.paths import AOI_GEOJSON, AOI_DIR

# Define Myanmar AOI bounding box (xmin, ymin, xmax, ymax)
BBOX = (95.5, 17.05, 98.4, 27.5)

def generate_bbox_geojson(bbox, output_path):
    print("Generating AOI GeoJSON...")
    geometry = box(*bbox)
    aoi_gdf = gpd.GeoDataFrame({"id": [1]}, geometry=[geometry], crs="EPSG:4326")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    aoi_gdf.to_file(output_path, driver="GeoJSON")
    print(f"✅ AOI saved to: {output_path}")

if __name__ == "__main__":
    generate_bbox_geojson(BBOX, AOI_GEOJSON)
