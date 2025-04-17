
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_DIR = os.path.join(DATA_DIR, "satellite", "raw")
PRE_EVENT_DIR = os.path.join(RAW_DIR, "pre_event")
POST_EVENT_DIR = os.path.join(RAW_DIR, "post_event")

PROCESSED_DIR = os.path.join(DATA_DIR, "satellite", "processed")
STACK_DIR = os.path.join(PROCESSED_DIR, "stacks")
INDICES_DIR = os.path.join(PROCESSED_DIR, "indices")

AOI_DIR = os.path.join(DATA_DIR, "aoi")
AOI_GEOJSON = os.path.join(AOI_DIR, "myanmar_aoi_bbox.geojson")

OSM_DIR = os.path.join(DATA_DIR, "osm")
OUTPUTS_DIR = os.path.join(PROJECT_ROOT, "outputs")
VISUALS_DIR = os.path.join(OUTPUTS_DIR, "visuals")
