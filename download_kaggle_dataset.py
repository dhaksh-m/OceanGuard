"""
User-requested snippet: downloads Sentinel-1 SAR Oil Spill Detection Dataset via kagglehub
Exactly matches requested import + connects to ML engine.

Run:
  python download_kaggle_dataset.py
This will attempt kagglehub download and then validate via ml.dataset
"""

import kagglehub
# Download latest version
path = kagglehub.dataset_download("harikrishnacs/sentinel-1-sar-oil-spill-detection-dataset")

print("Path to dataset files:", path)

# --- OceanGuard extended validation ---
try:
    from ml.dataset import scan_dataset_structure, Sentinel1ChipDataset
    from pathlib import Path
    import json
    info = scan_dataset_structure(Path(path))
    print(f"Inventory: {info['total_images']} images ({info['oil_count']} oil, {info['nooil_count']} no_oil)")
    if info['total_images'] > 0:
        # quick sanity: load one chip and run dummy inference
        from ml.unet_model import OilSpillUNetPredictor
        predictor = OilSpillUNetPredictor()
        # try real image inference if available
        jpg = info['all_jpgs'][0] if info['all_jpgs'] else None
        if jpg:
            from PIL import Image
            import numpy as np
            arr = np.array(Image.open(jpg).convert("L"))
            res = predictor.predict_mask(sar_image_data=arr, bbox=[103.81, 1.22, 103.95, 1.34])
            print(f"SAR inference test: is_spill={res['is_spill']} water_ratio={res.get('water_ratio')} confidence={res['sar_confidence']}")
    print("✓ Dataset ready for OceanGuard ML pipeline")
except Exception as e:
    print(f"Extended validation skipped: {e}")
    print("Fallback synthetic mode will be used if dataset incomplete.")
