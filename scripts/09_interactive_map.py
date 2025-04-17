import os
import geopandas as gpd
import folium
from folium.plugins import Fullscreen

# Define project root and relevant directories
PROJECT_ROOT = "/home/exouser/Downloads/Myanmar_Earthquake-Change_Detection"
PATCH_STATS_BASE = os.path.join(PROJECT_ROOT, "data", "processed", "patch_stats")
OUTPUT_MAP = os.path.join(PROJECT_ROOT, "outputs", "maps_interactive", "map_grouped.html")

# Mapping index types to user-friendly names
INDEX_TYPES = {
    "ndvi": "Vegetation (NDVI)",
    "ndbi": "Built-Up (NDBI)",
    "ndwi": "Water (NDWI)",
}

# Create folium map
m = folium.Map(location=[20.5, 96.5], zoom_start=6, tiles="OpenStreetMap")
Fullscreen().add_to(m)

# Add FeatureGroups for each index type
index_groups = {}
for short_name, long_name in INDEX_TYPES.items():
    fg = folium.FeatureGroup(name=long_name, show=False)
    index_groups[short_name] = fg
    fg.add_to(m)

    folder = os.path.join(PATCH_STATS_BASE, short_name)
    for file in os.listdir(folder):
        if file.endswith(".geojson"):
            tile_id = os.path.splitext(file)[0].replace("patch_stats_", "")
            gdf = gpd.read_file(os.path.join(folder, file))
            bounds = gdf.total_bounds  # minx, miny, maxx, maxy
            center_lat = (bounds[1] + bounds[3]) / 2
            center_lon = (bounds[0] + bounds[2]) / 2

            # Polygon overlay
            folium.GeoJson(
                gdf,
                name=f"{long_name} — {tile_id}",
                tooltip=folium.GeoJsonTooltip(fields=["mean_diff"]),
                style_function=lambda feature: {
                    "fillColor": "#00000000",
                    "color": "black",
                    "weight": 0.5,
                },
            ).add_to(fg)

            # Zoom-to patch marker
            folium.Marker(
                location=[center_lat, center_lon],
                popup=f"Zoom to {tile_id}",
                icon=folium.Icon(color="blue", icon="info-sign"),
            ).add_to(fg)

# Add OSM layer control
folium.LayerControl(collapsed=False).add_to(m)

# Save map to file
os.makedirs(os.path.dirname(OUTPUT_MAP), exist_ok=True)
m.save(OUTPUT_MAP)

OUTPUT_MAP
