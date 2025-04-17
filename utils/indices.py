import numpy as np

def compute_ndvi(stack):
    red, nir = stack[2].astype(float), stack[3].astype(float)
    return safe_index(nir, red)

def compute_ndbi(stack):
    swir, nir = stack[4].astype(float), stack[3].astype(float)
    return safe_index(swir, nir)

def compute_ndwi(stack):
    green, nir = stack[1].astype(float), stack[3].astype(float)
    return safe_index(green, nir)

def safe_index(b1, b2):
    with np.errstate(divide='ignore', invalid='ignore'):
        index = (b1 - b2) / (b1 + b2)
        index[np.isnan(index)] = 0
    return index

INDEX_FUNCS = {
    "ndvi": compute_ndvi,
    "ndbi": compute_ndbi,
    "ndwi": compute_ndwi,
}
