#!/usr/bin/env python3
# scripts/01_download_sentinel.py

'''
This script downloads Sentinel-2 pre- and post-event products from Copernicus using EODAG.

Requirements from the User:
1. Update the list of product IDs below (PRE_EVENT_PRODUCTS and POST_EVENT_PRODUCTS).
2. Set environment variables for Copernicus credentials:
    export EODAG__COP_DATASPACE__AUTH__CREDENTIALS__USERNAME="your Copernicus email"
    export EODAG__COP_DATASPACE__AUTH__CREDENTIALS__PASSWORD="your Copernicus password"
3. Ensure ~1GB per tile of free disk space.
4. Be patient – each tile may take a few minutes to download and extract.
'''

import shutil
import tempfile
import zipfile
import os
import sys
from tqdm import tqdm
from eodag import EODataAccessGateway

# Make script path-independent
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
from config.paths import PRE_EVENT_DIR, POST_EVENT_DIR

# Sentinel-2 Product IDs (customize below)
PRE_EVENT_PRODUCTS = [
    "S2B_MSIL2A_20250327T035539_N0511_R004_T47QKV_20250327T073409",
    "S2B_MSIL2A_20250327T035539_N0511_R004_T46QHE_20250327T073409",
]

POST_EVENT_PRODUCTS = [
    "S2C_MSIL2A_20250401T035601_N0511_R004_T47QKV_20250401T091413",
    "S2C_MSIL2A_20250401T035601_N0511_R004_T46QHE_20250401T091413",
]

PRODUCT_TYPE = "S2_MSI_L2A"
PROVIDER = "cop_dataspace"

def folder_already_exists(download_dir, product_id):
    safe_name = f"{product_id}.SAFE"
    raw_name = product_id
    for name in [safe_name, raw_name]:
        path = os.path.join(download_dir, name)
        if os.path.exists(path) and os.path.isdir(path):
            return True
    return False

def download_products(product_list, download_dir, label):
    print(f"\n=== Starting download: {label.upper()} ===")
    gateway = EODataAccessGateway()
    gateway.set_preferred_provider(PROVIDER)
    os.makedirs(download_dir, exist_ok=True)

    success, skipped, search_fail, download_fail = [], [], [], []

    for i, raw_id in enumerate(tqdm(product_list, desc=f"[{label}] Downloading", unit="product")):
        product_id = raw_id.replace(".SAFE", "")  # Normalize
        print(f"\n[{label}] {i+1}/{len(product_list)}: {product_id}")
        expected_folder = os.path.join(download_dir, f"{product_id}.SAFE")

        # ✅ Skip if .SAFE or raw folder already exists
        if folder_already_exists(download_dir, product_id):
            print(f"Already exists: {product_id}")
            skipped.append(product_id)
            continue

        try:
            results = gateway.search(provider=PROVIDER, productType=PRODUCT_TYPE, id=product_id)
            if not results:
                print(f"❌ Not found: {product_id}")
                search_fail.append(product_id)
                continue

            print(f"✅ Found: {results[0].properties.get('title', product_id)}")

            # ✅ Step 2: Download ZIP only
            zip_paths = gateway.download_all(results, extract=False)
            zip_path = zip_paths[0] if zip_paths else None

            if not zip_path or not zip_path.endswith(".zip"):
                print(f"❌ No ZIP returned for {product_id}")
                download_fail.append(product_id)
                continue

            print(f"Downloaded ZIP: {zip_path}")

            # ✅ Step 3: Extract ZIP to temp
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                extract_dir = tempfile.gettempdir()
                zip_ref.extractall(extract_dir)
                print(f"Extracted to temp: {extract_dir}")

            # ✅ Step 4: Locate .SAFE folder in temp
            safe_candidates = [
                os.path.join(extract_dir, d) for d in os.listdir(extract_dir)
                if d.endswith(".SAFE") and product_id in d
            ]

            if not safe_candidates:
                print(f"❌ No .SAFE folder found after extraction")
                download_fail.append(product_id)
                continue

            safe_folder = safe_candidates[0]
            print(f" Moving from temp: {safe_folder}")
            shutil.move(safe_folder, expected_folder)

            print(f"✅ Moved to: {expected_folder}")
            success.append(product_id)

        except Exception as e:
            print(f"❌ Error downloading {product_id}: {e}")
            download_fail.append(product_id)

    # 📊 Summary
    print(f"\n=== Summary for {label.upper()} ===")
    print(f"✅ Successful: {len(success)}")
    print(f" Skipped (already present): {len(skipped)}")
    print(f" Not found: {len(search_fail)}")
    print(f"❌ Failed downloads: {len(download_fail)}")
    if search_fail: print("  Not found:", search_fail)
    if download_fail: print("  Failed:", download_fail)

if __name__ == "__main__":
    username = os.getenv("EODAG__COP_DATASPACE__AUTH__CREDENTIALS__USERNAME")
    password = os.getenv("EODAG__COP_DATASPACE__AUTH__CREDENTIALS__PASSWORD")

    if not username or not password:
        print("❌ Missing EODAG Copernicus credentials in environment variables.")
        print("Set EODAG__COP_DATASPACE__AUTH__CREDENTIALS__USERNAME and PASSWORD.")
        exit(1)

    download_products(PRE_EVENT_PRODUCTS, PRE_EVENT_DIR, "pre_event")
    download_products(POST_EVENT_PRODUCTS, POST_EVENT_DIR, "post_event")

    print("\n Download script complete.")
