# Myanmar Earthquake 2025: Change Detection using Sentinel-2 Imagery + ML

> A reproducible geospatial machine learning pipeline to detect earthquake impact using Sentinel-2 imagery and OpenStreetMap data.

**Earthquake Date:** March 28, 2025  
**AOI:** 50km radius around epicenter (Mandalay) in Myanmar  
**Goal:** Identify damaged zones, infrastructure vulnerability, and prioritize emergency response using ML.

---

## Project Overview

This project uses pre- and post-earthquake Sentinel-2 imagery to detect changes via spectral indices (NDVI, NDBI, NDWI), quantify impact at patch level, classify damage zones using ML, and overlay infrastructure from OpenStreetMap for impact-aware response.

It is built to be:
- Fully reproducible  
- Modular (scripts are phase-based)  
- Impact-focused (detects building/infrastructure damages)  
- Visualization-ready (optional Streamlit/Dash deployment)

---

## Pipeline Overview

### Phase 1: Data Ingestion + Preprocessing
- Download Sentinel-2 images using [EODAG](https://github.com/CS-SI/eodag). Please use 01_download_sentinel and change the tile codes if required
- Filter by <10% cloud cover
- Clip to AOI (bounding box of epicenter + 50km)
- Resample 20m bands to 10m

### Phase 2: Generate Bounding Box
- Run 02_generate_aoi_bbox.py. Use a bounding box with the required area for clipping.

### Phase 3: Download OSM data
- Download Open Street Map (OSM) data. The bounding box will be used here.

### Phase 4: Create stacked data for indicing
- Stacked data will be created for further processing

### Phase 5: Indice Calculation
- Compute index differences per patch
- Flag anomalous patches using thresholds/statistics
- NDBI, NDWI, NDVI processing is done here

### Phase 6: Visualize Indices
- Visualize the processed areas

### Phase 7: Stats for the Patches
- Stats for the patches are calculated here

### Phase 8: Output
- The patches are plotted on a map.

### Phase 9: Interactive Map
- Finally, overlay on a map to create an html file.
---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/nithingm/Myanmar_Earthquake_Change_Detection.git
cd Myanmar_Earthquake_Change_Detection
```

### 2. Set Up the Environment

We recommend using [`uv`](https://astral.sh/blog/uv/) (ultrafast Python installer):

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

Alternatively, using `conda`:

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

Just scripts/run 00_run_pipelines.py

## Sentinel-2 Bands Used

| Band | Name        | Resolution | Use              |
|------|-------------|------------|------------------|
| B02  | Blue        | 10m        | NDBI, NDWI       |
| B03  | Green       | 10m        | NDWI             |
| B04  | Red         | 10m        | NDVI             |
| B08  | NIR         | 10m        | NDVI             |
| B11  | SWIR        | 20m → 10m  | NDBI             |
| B12  | SWIR-2      | 20m → 10m  | NDBI             |

---

## Area of Interest (AOI)

Bounding box centered around the epicenter:

```
North: 27.5
South: 17.05
East: 98.4
West: 95.5
```

Stored in: `data/aoi/myanmar_aoi_bbox.geojson`

---

## Future Work

- Integrate UNOSAT or Maxar post-disaster maps
- Use road network centrality to prioritize rescue zones
- Improve classification using transfer learning
- Live dashboard for humanitarian response teams

---

## Sample Outputs

| ∆NDVI Map | ∆NDBI Map | Classified Damage |
|-----------|-----------|-------------------|
| ![](outputs/sample_dndvi.png) | ![](outputs/sample_dndbi.png) | ![](outputs/sample_damage_map.png) |

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.


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