
import rasterio
import numpy as np
import os

def read_raster(path):
    with rasterio.open(path) as src:
        return src.read(), src.meta

def write_raster(path, array, meta, dtype="float32", count=1):
    meta.update({
        "count": count,
        "dtype": dtype
    })
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with rasterio.open(path, "w", **meta) as dst:
        if count == 1:
            dst.write(array.astype(dtype), 1)
        else:
            for i in range(count):
                dst.write(array[i].astype(dtype), i + 1)
