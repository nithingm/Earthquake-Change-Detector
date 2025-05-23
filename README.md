# Myanmar Earthquake 2025: Change Detection using Sentinel-2 Imagery + ML

> A reproducible geospatial machine learning pipeline to detect earthquake impact in Myanmar using Sentinel-2 satellite data and OpenStreetMap features.

**Earthquake Date:** March 28, 2025  
**AOI:** 50km radius around epicenter (Mandalay) in Myanmar  
**Goal:** Identify damaged zones, infrastructure vulnerability, and prioritize emergency response using ML and geospatial analysis.

---

## Project Overview

This project performs change detection using pre- and post-earthquake Sentinel-2 imagery. It computes spectral indices (NDVI, NDBI, NDWI), generates difference maps, performs patch-level statistical analysis, and visualizes the impact with overlays from OpenStreetMap (OSM). The outputs include static difference maps, patch-wise heatmaps, and an interactive web map.

The pipeline is:
- Fully reproducible
- Modular (scripted in distinct steps)
- Impact-focused (vegetation, water, built-up changes)
- Integrated with OSM for infrastructure awareness
- Visualization-ready (static plots and Folium maps)

---

## Pipeline Overview

### Phase 1: Data Ingestion + Preprocessing
- Download Sentinel-2 pre/post-event data using `01_download_sentinel.py`
- Product IDs are set inside the script; change as needed
- Filtered by <10% cloud cover

### Phase 2: Generate Bounding Box
- Run `02_generate_aoi_bbox.py` to define the AOI for Mandalay + 50km buffer

### Phase 3: Download OSM Data
- Use `03_download_osm_data.py` to download roads, hospitals, landuse, and other key infrastructure layers

### Phase 4: Clip and Stack Bands
- Use `04_clip_and_stack.py` to clip all bands to AOI and stack them
- Resamples 20m bands to 10m resolution

### Phase 5: Compute Indices (NDVI, NDBI, NDWI)
- `05_compute_indices.py` computes indices and generates difference maps (Post - Pre)
- Difference rasters are reprojected to EPSG:4326

### Phase 6: Visualize Indices
- `06_visualize_indices.py` saves side-by-side static maps for pre, post, and diff

### Phase 7: Patch-wise Stats
- `07_patch_stats.py` divides diff rasters into 128x128 pixel patches and computes average change
- Outputs saved as GeoJSON and CSV

### Phase 8: Plot Patch Stats
- `08_plot_patch_stats.py` renders patch maps with diverging color maps for each index

### Phase 9: Interactive Map
- `09_interactive_map.py` builds a layer-controlled Folium map grouping patch data by index
- Output: `outputs/maps_interactive/map_grouped.html`

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/nithingm/Myanmar_Earthquake_Change_Detection.git
cd Myanmar_Earthquake_Change_Detection
```

### 2. Set Up the Environment

Using [`uv`](https://astral.sh/blog/uv/):

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

Or using `conda`:

```bash
conda create -n myanmar_eq python=3.10 -y
conda activate myanmar_eq
pip install -r requirements.txt
```

### 3. Set EODAG Credentials

```bash
export EODAG__COP_DATASPACE__AUTH__CREDENTIALS__USERNAME="your_copernicus_username"
export EODAG__COP_DATASPACE__AUTH__CREDENTIALS__PASSWORD="your_copernicus_password"
```

---

## Running the Pipeline

Use the master runner script:

```bash
python scripts/00_run_pipeline.py
```

This sequentially runs:
1. Sentinel download
2. AOI generation
3. OSM data fetch
4. Clipping + stacking
5. Index computation
6. Static visualizations
7. Patch Stats
8. Plot Patch Stats
9. Interactive Map

---

## Sentinel-2 Bands Used

| Band | Name        | Resolution | Use              |
|------|-------------|------------|------------------|
| B02  | Blue        | 10m        | NDBI, NDWI       |
| B03  | Green       | 10m        | NDWI             |
| B04  | Red         | 10m        | NDVI             |
| B08  | NIR         | 10m        | NDVI, NDWI       |
| B11  | SWIR        | 20m → 10m  | NDBI, NDWI       |
| B12  | SWIR-2      | 20m → 10m  | NDBI             |

---

## Area of Interest (AOI)

Bounding box used:
```
North: 27.5
South: 17.05
East: 98.4
West: 95.5
```
File: `data/aoi/myanmar_aoi_bbox.geojson`
---

## Future Work

- Integrate Maxar/UNOSAT post-disaster building data
- Estimate infrastructure damage severity from index scores
- Add classification model (CNN) for binary damage prediction
- Build emergency response prioritization tool

---

## References

- [Copernicus Open Access Hub](https://scihub.copernicus.eu/)
- [EODAG](https://github.com/CS-SI/eodag)
- [OSM Overpass API](https://overpass-api.de/)
- [UNOSAT Damage Assessments](https://www.unitar.org/maps)

---

## License

[MIT License](LICENSE)

---

## Author

Developed by [Nithin George](https://github.com/nithingm)  
_ML for Impact | Geospatial AI | Disaster Response_

