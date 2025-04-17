#!/usr/bin/env python3
# scripts/03_download_osm_data.py

"""
Robust version: Downloads OSM features tag-by-tag using AOI from GeoJSON.
Stores cache in: data/osm/cache
Outputs each layer to: data/osm/osm_<tag>.geojson
"""

import os
import sys
import geopandas as gpd
import osmnx as ox
from shapely.geometry import box

# Setup config paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
from config.paths import AOI_GEOJSON, OSM_DIR

# Set cache inside project
ox.settings.use_cache = True
ox.settings.cache_folder = os.path.join(OSM_DIR, "cache")
os.makedirs(ox.settings.cache_folder, exist_ok=True)

# Each of these will be queried individually
TAGS = {
    "building": True,
    "highway": True,
    "landuse": True,
    "waterway": True,
    "natural": "water",
    "amenity": True,
    "leisure": True,
    "man_made": True,
    "railway": True,
    "public_transport": True,
    "healthcare": True
}

def get_bbox_polygon(aoi_path):
    gdf = gpd.read_file(aoi_path)
    minx, miny, maxx, maxy = gdf.total_bounds
    return (minx, miny, maxx, maxy), box(minx, miny, maxx, maxy)

def query_and_save(tag_key, tag_value, polygon):
    print(f"Fetching: {tag_key} = {tag_value}")
    try:
        tag = {tag_key: tag_value}
        gdf = ox.features_from_polygon(polygon=polygon, tags=tag)
        if not gdf.empty:
            out_path = os.path.join(OSM_DIR, f"osm_{tag_key}.geojson")
            gdf.to_file(out_path, driver="GeoJSON")
            print(f"✅ Saved {tag_key} → {out_path}")
        else:
            print(f"⚠️ No data found for {tag_key}")
    except Exception as e:
        print(f"❌ Error fetching {tag_key}: {e}")

def main():
    print("📍 Reading AOI from:", AOI_GEOJSON)
    bbox, polygon = get_bbox_polygon(AOI_GEOJSON)
    print(f"BBOX: {bbox}")

    os.makedirs(OSM_DIR, exist_ok=True)

    for tag_key, tag_value in TAGS.items():
        query_and_save(tag_key, tag_value, polygon)

    print("\nAll OSM layers fetched successfully.")

if __name__ == "__main__":
    main()
