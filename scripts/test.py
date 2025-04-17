import rasterio
src = rasterio.open("/home/exouser/Downloads/Myanmar_Earthquake-Change_Detection/data/satellite/processed/stacks/post/S2C_MSIL2A_20250401T035601_N0511_R004_T47QKV_20250401T091413_stack.tif")
print("Bounds:", src.bounds)
print("CRS:", src.crs)
import geopandas as gpd
aoi = gpd.read_file("/home/exouser/Downloads/Myanmar_Earthquake-Change_Detection/data/aoi/myanmar_aoi_bbox.geojson")
aoi = aoi.to_crs(src.crs)
print("AOI bounds (transformed):", aoi.total_bounds)

from rasterio.warp import transform_bounds

with rasterio.open("/home/exouser/Downloads/Myanmar_Earthquake-Change_Detection/data/satellite/processed/indices/ndbi/diff/T47QKV_diff.tif") as src:
    bounds = src.bounds
    crs = src.crs
    wgs_bounds = transform_bounds(crs, "EPSG:4326", *bounds)

print("EPSG:32646 Bounds:", bounds)
print("Transformed to EPSG:4326:", wgs_bounds)


