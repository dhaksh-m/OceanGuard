"""
OceanGuard ML Configuration
Centralizes hyperparameters, paths, and ocean-aware filtering knobs.
"""
import os
from pathlib import Path

# Root paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ML_ROOT = PROJECT_ROOT / "ml"
DATA_ROOT = PROJECT_ROOT / "data"
CHECKPOINT_ROOT = PROJECT_ROOT / "checkpoints"

# Kaggle dataset
KAGGLE_DATASET_ID = "harikrishnacs/sentinel-1-sar-oil-spill-detection-dataset"
KAGGLE_DATASET_CACHE = DATA_ROOT / "kaggle_sentinel1"

# Model
MODEL_VERSION = "v2.1-oceanguard-unet-landmasked"
INPUT_SIZE = 400  # dataset chip size is 400x400
NUM_CLASSES = 1
THRESHOLD = 0.52
OCEAN_ONLY_STRICT = True
MIN_WATER_RATIO = 0.80  # predicted spill must be >=80% over water, else rejected
LOOKALIKE_THRESHOLD = 0.32

# Training
BATCH_SIZE = 16
EPOCHS = 25
LR = 1e-4
WEIGHT_DECAY = 1e-5
AUGMENT = True

# SAR preprocessing
SAR_NORMALIZE_MEAN = 0.45
SAR_NORMALIZE_STD = 0.22
SPECKLE_FILTER = "lee"  # lee | gamma-map | none

# Land mask
LAND_MASK_SOURCE = "osm-coastline-simplified"  # simplified polygons + OSM fallback
# Hard safety: never report spill if centroid falls on land bounding boxes
LAND_SUPPRESSION_ENABLED = True

# Attribution / Ocean
DRIFT_WIND_LEEWAY = 0.03
