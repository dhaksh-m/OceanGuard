"""
OceanGuard SAR Preprocessing Pipeline
Handles Sentinel-1 IW GRDH VV/VH calibration chain for Oil Spill detection.
Designed to be lightweight, torch-optional, and to produce normalized tensors ready for UNet.
"""
import numpy as np
from typing import Tuple, Optional
try:
    import cv2
    HAS_CV2 = True
except Exception:
    HAS_CV2 = False

def lee_speckle_filter(img: np.ndarray, window_size: int = 7, sigma: float = 0.9) -> np.ndarray:
    """Simple Lee speckle filter approximation without external deps."""
    if HAS_CV2:
        # Use OpenCV bilateral + box as approximation
        mean = cv2.blur(img, (window_size, window_size))
        sqr_mean = cv2.blur(img**2, (window_size, window_size))
        variance = sqr_mean - mean**2
        # Lee coefficient
        k = variance / (variance + sigma**2 + 1e-8)
        return mean + k * (img - mean)
    else:
        # NumPy fallback: local mean via uniform filter emulation
        # Very simplified
        try:
            from scipy.ndimage import uniform_filter
            mean = uniform_filter(img, size=window_size)
            sqr_mean = uniform_filter(img**2, size=window_size)
            var = sqr_mean - mean**2
            k = var / (var + sigma**2 + 1e-9)
            return mean + k * (img - mean)
        except Exception:
            return img

def radiometric_calibrate(sar_raw: np.ndarray, calibration_factor: float = 1.0) -> np.ndarray:
    """Convert digital numbers to sigma0 in dB (approx)."""
    # Clip raw to avoid log of zero
    eps = 1e-8
    sigma0_linear = np.clip(sar_raw.astype(np.float32) / 65535.0 * calibration_factor, eps, None)
    sigma0_db = 10.0 * np.log10(sigma0_linear + eps)
    # Normalize dB range roughly -25 to 5 dB -> 0..1
    sigma0_db_clipped = np.clip(sigma0_db, -25.0, 5.0)
    sigma0_norm = (sigma0_db_clipped + 25.0) / 30.0
    return sigma0_norm.astype(np.float32)

def normalize_sar(sar_img: np.ndarray, mean: float = 0.45, std: float = 0.22) -> np.ndarray:
    return (sar_img - mean) / (std + 1e-8)

def resize_and_pad(sar_img: np.ndarray, target_size: int = 400) -> np.ndarray:
    """Center crop/pad to target_size x target_size."""
    h, w = sar_img.shape[:2]
    if HAS_CV2:
        if h != target_size or w != target_size:
            sar_resized = cv2.resize(sar_img, (target_size, target_size), interpolation=cv2.INTER_LINEAR)
            return sar_resized
        return sar_img
    else:
        # PIL fallback
        try:
            from PIL import Image
            mode = "F" if sar_img.dtype == np.float32 else "L"
            pil_img = Image.fromarray((sar_img*255).astype(np.uint8) if sar_img.max()<=1 else sar_img.astype(np.uint8))
            pil_res = pil_img.resize((target_size, target_size), Image.BILINEAR)
            arr = np.array(pil_res).astype(np.float32) / 255.0
            return arr
        except Exception:
            return sar_img

def preprocess_sar_chip(sar_raw: np.ndarray, target_size: int = 400, apply_speckle: bool = True) -> np.ndarray:
    """
    Full pipeline: calibrate -> speckle filter -> resize -> normalize -> CHW tensor.
    Input: sar_raw as HxW uint8/uint16 or float (0-255 or 0-65535)
    Output: 1xHxW float32 normalized
    """
    # Ensure 2D grayscale
    if sar_raw.ndim == 3:
        # Take VV channel (first)
        sar_raw = sar_raw[..., 0]
    # Calibrate
    calibrated = radiometric_calibrate(sar_raw)
    if apply_speckle:
        calibrated = lee_speckle_filter(calibrated)
    resized = resize_and_pad(calibrated, target_size)
    normalized = normalize_sar(resized)
    # Add channel dim
    if normalized.ndim == 2:
        normalized = normalized[None, :, :]  # 1 x H x W
    return normalized

def augment_chip(img: np.ndarray, mask: Optional[np.ndarray] = None) -> Tuple[np.ndarray, Optional[np.ndarray]]:
    """Lightweight augmentation: flips, rotation."""
    if np.random.rand() < 0.5:
        img = np.flip(img, axis=2).copy()
        if mask is not None:
            mask = np.flip(mask, axis=1).copy()
    if np.random.rand() < 0.5:
        img = np.flip(img, axis=1).copy()
        if mask is not None:
            mask = np.flip(mask, axis=0).copy()
    # Random 90-degree rotation
    k = np.random.randint(0, 4)
    if k != 0:
        img = np.rot90(img, k, axes=(1,2)).copy()
        if mask is not None:
            mask = np.rot90(mask, k).copy()
    return img, mask

def batch_to_model_input(sar_batch: np.ndarray) -> np.ndarray:
    """
    Convert uint8 JPEG batch (B,H,W) to normalized CHW float for模型.
    This mirrors preprocess but for already-decoded JPEGs which are 0-255 grayscale.
    """
    # sar_batch is B x H x W uint8
    float_batch = sar_batch.astype(np.float32) / 255.0
    # Invert dark slick intuition: oil appears dark (low backscatter) -> model learns dark features
    # Keep as is, normalize
    normed = (float_batch - 0.45) / 0.22
    # Add channel dim
    normed = normed[:, None, :, :]  # B x 1 x H x W
    return normed
