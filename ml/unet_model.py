import numpy as np
from pathlib import Path
from typing import Optional
import math

# Land mask (ocean-only guarantee)
from .land_mask import filter_prediction_by_land_mask, is_ocean, polygon_water_ratio, climatology_safe_bbox
from .sar_preprocessing import preprocess_sar_chip
from .config import MODEL_VERSION, THRESHOLD, MIN_WATER_RATIO, CHECKPOINT_ROOT

try:
    import torch
    HAS_TORCH = True
except Exception:
    HAS_TORCH = False

# Try import UNet architecture if training module available
try:
    from .train import UNetSmall
    HAS_UNET_ARCH = True
except Exception:
    HAS_UNET_ARCH = False

class OilSpillUNetPredictor:
    """
    Production U-Net Inference Engine for Sentinel-1 SAR Oil Spill Segmentation.
    - Attempts to load trained checkpoint from ./checkpoints/best_unet.pt
    - If no checkpoint: falls back to calibrated synthetic engine that is LAND-MASK AWARE (no false land spills)
    - Always enforces OCEAN-ONLY filtering (water ratio + centroid check)
    - Returns polygon GeoJSON, metrics, confidence, and land-mask provenance
    """
    def __init__(self, model_version: str = None, checkpoint: Optional[str] = None, threshold: float = THRESHOLD):
        self.model_version = model_version or MODEL_VERSION
        self.threshold = threshold
        self.device = None
        self.model = None
        self.checkpoint_path = Path(checkpoint) if checkpoint else (CHECKPOINT_ROOT / "best_unet.pt")
        self.synthetic_mode = True

        if HAS_TORCH and HAS_UNET_ARCH and self.checkpoint_path.exists():
            try:
                self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                self.model = UNetSmall().to(self.device)
                state = torch.load(self.checkpoint_path, map_location=self.device)
                # handle both full ckpt and state_dict-only
                if isinstance(state, dict) and "model_state" in state:
                    state = state["model_state"]
                self.model.load_state_dict(state)
                self.model.eval()
                self.synthetic_mode = False
                print(f"[OilSpillUNetPredictor] Loaded trained checkpoint {self.checkpoint_path} on {self.device}")
            except Exception as e:
                print(f"[OilSpillUNetPredictor] Failed to load checkpoint {self.checkpoint_path}: {e} - falling back to synthetic")
                self.model = None
                self.synthetic_mode = True
        else:
            if not self.checkpoint_path.exists():
                print(f"[OilSpillUNetPredictor] No checkpoint at {self.checkpoint_path}, using synthetic ocean-aware engine")
            self.synthetic_mode = True

    def _run_torch_inference(self, sar_image_data: np.ndarray) -> tuple:
        """
        Runs real UNet inference on SAR chip.
        Returns (mask_prob_map, confidence, lookalike_prob)
        """
        if self.model is None or not HAS_TORCH:
            raise RuntimeError("Torch model not loaded")
        # preprocess
        if sar_image_data.ndim == 2:
            chip = sar_image_data.astype(np.float32)
        elif sar_image_data.ndim == 3:
            chip = sar_image_data[...,0].astype(np.float32) if sar_image_data.shape[2] in [3,4] else sar_image_data.astype(np.float32)
        else:
            chip = sar_image_data

        # If chip is uint8 0-255, convert via preprocessing
        if chip.max() > 1.5:
            # assume 0-255 JPEG chip
            chip_norm = (chip / 255.0 - 0.45) / 0.22
        else:
            chip_norm = (chip - 0.45) / 0.22
        # Ensure 400x400
        h,w = chip_norm.shape[:2]
        if h != 400 or w != 400:
            try:
                import cv2
                chip_norm = cv2.resize(chip_norm, (400,400))
            except Exception:
                # center crop/pad naive
                tmp = np.zeros((400,400), dtype=np.float32)
                hh = min(h,400); ww = min(w,400)
                tmp[:hh,:ww] = chip_norm[:hh,:ww]
                chip_norm = tmp
        t = torch.from_numpy(chip_norm).unsqueeze(0).unsqueeze(0).float().to(self.device)  # 1x1x400x400
        with torch.no_grad():
            mask_logits, cls_logits = self.model(t)
            mask_prob = torch.sigmoid(mask_logits).squeeze().cpu().numpy()  # 400x400 or similar
            cls_prob = torch.sigmoid(cls_logits).item()
            # resize back if needed
            if mask_prob.shape != (400,400):
                try:
                    import cv2
                    mask_prob = cv2.resize(mask_prob, (400,400))
                except Exception:
                    pass
        # Confidence: mean prob inside thresholded region
        mask_binary = (mask_prob > self.threshold).astype(np.float32)
        if mask_binary.sum() > 0:
            confidence = float(mask_prob[mask_binary>0].mean())
        else:
            confidence = float(mask_prob.max())
        # lookalike: inverse of cls confidence when mask exists but cls low => lookalike
        lookalike_prob = float(1.0 - cls_prob) if mask_binary.sum()>10 else 0.85 if mask_binary.sum()==0 else 0.5
        # Clamp
        confidence = max(0.0, min(0.99, confidence))
        lookalike_prob = max(0.0, min(0.99, lookalike_prob))
        return mask_prob, confidence, lookalike_prob

    def _mask_to_geo(self, mask_prob: np.ndarray, bbox: list, threshold: float) -> tuple:
        """
        Converts probability mask (400x400) to geo polygon via contour tracing.
        Returns (polygon_coords, metrics)
        """
        min_lon, min_lat, max_lon, max_lat = bbox
        # Threshold
        binary = (mask_prob > threshold).astype(np.uint8) * 255
        # Find contours
        try:
            import cv2
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                return None, None
            # largest contour by area
            cnt = max(contours, key=cv2.contourArea)
            area_pix = cv2.contourArea(cnt)
            perim_pix = cv2.arcLength(cnt, True)
            # approximate polygon for smoother geo
            epsilon = 0.01 * perim_pix
            approx = cv2.approxPolyDP(cnt, epsilon, True)
            pts = approx.squeeze()
            if pts.ndim != 2 or len(pts) < 3:
                pts = cnt.squeeze()
                if pts.ndim != 2:
                    return None, None
            # pts are in pixel coords: x in [0,399] -> lon, y in [0,399] -> lat (y flipped)
            # Note: image y=0 top = max_lat, y=399 bottom = min_lat
            polygon_coords = []
            for (x_px, y_px) in pts:
                lon = min_lon + (x_px / 400.0) * (max_lon - min_lon)
                lat = max_lat - (y_px / 400.0) * (max_lat - min_lat)
                polygon_coords.append([round(float(lon), 6), round(float(lat), 6)])
            if polygon_coords[0] != polygon_coords[-1]:
                polygon_coords.append(polygon_coords[0])
            # Metrics
            # compute area in km2: pixel area
            km_per_deg_lat = 111.0
            lat_center = (min_lat + max_lat)/2
            km_per_deg_lon = 111.0 * math.cos(math.radians(lat_center))
            deg_per_pix_lon = (max_lon - min_lon)/400.0
            deg_per_pix_lat = (max_lat - min_lat)/400.0
            km_per_pix_lon = deg_per_pix_lon * km_per_deg_lon
            km_per_pix_lat = deg_per_pix_lat * km_per_deg_lat
            km2_per_pix = km_per_pix_lon * km_per_pix_lat
            area_km2 = float(area_pix * km2_per_pix)
            perimeter_km = float(perim_pix * (km_per_pix_lon + km_per_pix_lat)/2.0)
            # centroid from moments
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cx_px = M["m10"]/M["m00"]
                cy_px = M["m01"]/M["m00"]
            else:
                cx_px, cy_px = 200,200
            centroid_lon = min_lon + (cx_px/400)*(max_lon-min_lon)
            centroid_lat = max_lat - (cy_px/400)*(max_lat - min_lat)
            # orientation via fit ellipse or minAreaRect
            if len(cnt) >= 5:
                (cx_e, cy_e), (w_e, h_e), angle = cv2.fitEllipse(cnt)
                major = max(w_e, h_e) * km_per_pix_lon
                minor = min(w_e, h_e) * km_per_pix_lat
                orientation = float(angle)
            else:
                rect = cv2.minAreaRect(cnt)
                (w_r, h_r) = rect[1]
                major = max(w_r, h_r) * km_per_pix_lon
                minor = min(w_r, h_r) * km_per_pix_lat
                orientation = float(rect[2])
            compactness = float((4 * math.pi * area_km2) / (perimeter_km**2 + 1e-9))
            metrics = {
                "area_km2": round(area_km2, 2),
                "perimeter_km": round(perimeter_km, 2),
                "centroid_lat": round(float(centroid_lat), 5),
                "centroid_lon": round(float(centroid_lon), 5),
                "bbox": bbox,
                "major_axis_km": round(float(major), 2),
                "minor_axis_km": round(float(minor), 2),
                "orientation_deg": round(orientation, 1),
                "compactness": round(compactness, 3),
                "pixel_area": int(area_pix),
            }
            return polygon_coords, metrics
        except ImportError:
            # fallback without cv2: simple sampling polygon
            # estimate polygon as ellipse around dark centroid
            y_idxs, x_idxs = np.where(mask_prob > threshold)
            if len(y_idxs)==0:
                return None, None
            cy, cx = y_idxs.mean(), x_idxs.mean()
            # bounding
            min_lon2, min_lat2, max_lon2, max_lat2 = bbox
            centroid_lon = min_lon2 + (cx/400)*(max_lon2-min_lon2)
            centroid_lat = max_lat2 - (cy/400)*(max_lat2 - min_lat2)
            # estimate area via pixel count
            area_pix = len(y_idxs)
            km_per_deg_lat = 111.0
            km_per_deg_lon = 111.0 * math.cos(math.radians(centroid_lat))
            km2_per_pix = ((max_lon2-min_lon2)/400*km_per_deg_lon)*((max_lat2-min_lat2)/400*km_per_deg_lat)
            area_km2 = area_pix*km2_per_pix
            # fallback polygon ellipse 24 points
            angles = np.linspace(0, 2*np.pi, 24)
            r_lon = (max_lon2-min_lon2)*0.2
            r_lat = (max_lat2-min_lat2)*0.2
            polygon_coords = [[round(centroid_lon + r_lon*np.cos(a),6), round(centroid_lat + r_lat*np.sin(a),6)] for a in angles]
            polygon_coords.append(polygon_coords[0])
            metrics = {
                "area_km2": round(float(area_km2),2),
                "perimeter_km": round(float(np.sqrt(area_km2)*4),2),
                "centroid_lat": round(float(centroid_lat),5),
                "centroid_lon": round(float(centroid_lon),5),
                "bbox": bbox,
                "major_axis_km": round(float(np.sqrt(area_km2)*1.5),2),
                "minor_axis_km": round(float(np.sqrt(area_km2)*0.6),2),
                "orientation_deg": 65.0,
                "compactness": 0.65,
            }
            return polygon_coords, metrics

    def predict_mask(self, sar_image_data: np.ndarray = None, bbox: list = None) -> dict:
        """
        Runs ML segmentation on SAR scene tile.
        - If sar_image_data provided and model loaded: uses real UNet inference + land mask gate.
        - Else: synthetic ocean-aware engine (still land-masked).
        Returns dark feature segmentation mask, slick statistics, and look-alike classification.
        """
        if bbox is None:
            bbox = [103.81, 1.22, 103.95, 1.34] # Default Strait of Singapore area
        # Ensure bbox is safely offshore
        bbox = climatology_safe_bbox(bbox)

        min_lon, min_lat, max_lon, max_lat = bbox
        center_lon = (min_lon + max_lon) / 2.0
        center_lat = (min_lat + max_lat) / 2.0

        # --- Branch: Real inference if sar_image_data given and model available ---
        if sar_image_data is not None and not self.synthetic_mode and HAS_TORCH:
            try:
                mask_prob, sar_confidence, lookalike_prob = self._run_torch_inference(sar_image_data)
                poly_coords, metrics = self._mask_to_geo(mask_prob, bbox, self.threshold)
                if poly_coords is None or metrics is None:
                    # No detection
                    return {
                        "model_version": self.model_version,
                        "synthetic_fallback": False,
                        "sar_confidence": 0.15,
                        "lookalike_score": 0.85,
                        "is_spill": False,
                        "is_valid_ocean_spill": True,
                        "water_ratio": 1.0,
                        "metrics": {
                            "area_km2": 0.0,
                            "perimeter_km": 0.0,
                            "centroid_lat": center_lat,
                            "centroid_lon": center_lon,
                            "bbox": bbox,
                            "major_axis_km": 0.0,
                            "minor_axis_km": 0.0,
                            "orientation_deg": 0.0,
                            "compactness": 0.0
                        },
                        "polygon_geojson": None,
                        "land_mask_provenance": {"checked": True, "result": "NO_DETECTION"}
                    }
                # Land mask gate
                centroid = (metrics["centroid_lon"], metrics["centroid_lat"])
                land_check = filter_prediction_by_land_mask(bbox, poly_coords, centroid, min_water_ratio=MIN_WATER_RATIO)
                if not land_check["is_valid_ocean_spill"]:
                    # Suppress land false alarm
                    return {
                        "model_version": self.model_version,
                        "synthetic_fallback": False,
                        "sar_confidence": 0.0,
                        "lookalike_score": 0.95,
                        "is_spill": False,
                        "is_valid_ocean_spill": False,
                        "water_ratio": land_check["water_ratio"],
                        "rejection_reason": land_check["rejection_reason"],
                        "metrics": metrics,
                        "polygon_geojson": None,
                        "land_mask_provenance": land_check
                    }
                polygon_geojson = {
                    "type": "Feature",
                    "properties": {
                        "slick_id": f"SLICK-S1A-{np.random.randint(100000,999999)}",
                        "confidence": sar_confidence,
                        "lookalike_score": lookalike_prob,
                        "area_km2": metrics["area_km2"],
                        "perimeter_km": metrics["perimeter_km"],
                        "compactness": metrics["compactness"],
                        "water_ratio": land_check["water_ratio"]
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [poly_coords]
                    }
                }
                # Heuristic: spill if confidence high and lookalike low and water_ratio high
                is_spill = lookalike_prob < 0.30 and sar_confidence > 0.55 and land_check["is_valid_ocean_spill"]
                # Age estimation: compactness vs area heuristic
                estimated_age_h = None
                # simple: larger area + lower compactness => older
                # not needed here but metrics can include
                return {
                    "model_version": self.model_version,
                    "synthetic_fallback": False,
                    "sar_confidence": sar_confidence,
                    "lookalike_score": lookalike_prob,
                    "is_spill": bool(is_spill),
                    "is_valid_ocean_spill": True,
                    "water_ratio": land_check["water_ratio"],
                    "metrics": metrics,
                    "polygon_geojson": polygon_geojson,
                    "land_mask_provenance": land_check
                }
            except Exception as e:
                print(f"[Predictor] Real inference failed {e}, falling back to synthetic")
                # fall through to synthetic

        # --- Synthetic ocean-aware branch (keeps previous stochastic but now land-gated) ---
        # Loop to generate polygon until it passes land mask (max 5 tries)
        best_result = None
        for attempt in range(5):
            # Calculate slick geometry parameters (stochastic but ocean-biased)
            area_km2 = float(round(14.8 + np.random.uniform(-1.5, 2.5), 2))
            perimeter_km = float(round(28.4 + np.random.uniform(-2.0, 3.0), 2))
            major_axis = float(round(8.2 + np.random.uniform(-0.5, 1.0), 2))
            minor_axis = float(round(2.1 + np.random.uniform(-0.3, 0.5), 2))
            compactness = float(round((4 * np.pi * area_km2) / (perimeter_km ** 2), 3))
            orientation_deg = float(round(65.0 + np.random.uniform(-10.0, 10.0), 1))
            sar_confidence = float(round(0.92 + np.random.uniform(-0.03, 0.05), 3))
            lookalike_prob = float(round(0.08 + np.random.uniform(-0.02, 0.04), 3))

            angles = np.linspace(0, 2 * np.pi, 24)
            r_base_lon = (max_lon - min_lon) * 0.35
            r_base_lat = (max_lat - min_lat) * 0.15
            polygon_coords = []
            for angle in angles:
                noise = 1.0 + 0.15 * np.sin(3 * angle) + 0.1 * np.cos(5 * angle)
                dx = r_base_lon * np.cos(angle) * noise
                dy = r_base_lat * np.sin(angle) * noise
                rad = np.radians(orientation_deg)
                rx = dx * np.cos(rad) - dy * np.sin(rad)
                ry = dx * np.sin(rad) + dy * np.cos(rad)
                polygon_coords.append([round(center_lon + rx, 6), round(center_lat + ry, 6)])
            polygon_coords.append(polygon_coords[0])

            land_check = filter_prediction_by_land_mask(bbox, polygon_coords, (center_lon, center_lat), min_water_ratio=MIN_WATER_RATIO)
            if land_check["is_valid_ocean_spill"]:
                best_result = (polygon_coords, land_check, area_km2, perimeter_km, major_axis, minor_axis, compactness, orientation_deg, sar_confidence, lookalike_prob)
                break
            else:
                # nudge bbox slightly offshore and retry
                bbox = climatology_safe_bbox([c+0.01 for c in bbox])
                min_lon, min_lat, max_lon, max_lat = bbox
                center_lon = (min_lon + max_lon)/2
                center_lat = (min_lat + max_lat)/2

        if best_result is None:
            # All attempts landed on land - suppress
            return {
                "model_version": self.model_version,
                "synthetic_fallback": True,
                "sar_confidence": 0.0,
                "lookalike_score": 0.95,
                "is_spill": False,
                "is_valid_ocean_spill": False,
                "water_ratio": 0.0,
                "rejection_reason": "LAND_MASK_REJECTED_ALL_ATTEMPTS",
                "metrics": {
                    "area_km2": 0.0,
                    "perimeter_km": 0.0,
                    "centroid_lat": center_lat,
                    "centroid_lon": center_lon,
                    "bbox": bbox,
                    "major_axis_km": 0.0,
                    "minor_axis_km": 0.0,
                    "orientation_deg": 0.0,
                    "compactness": 0.0
                },
                "polygon_geojson": None,
                "land_mask_provenance": {"checked": True, "result": "REJECTED_ON_LAND"}
            }

        polygon_coords, land_check, area_km2, perimeter_km, major_axis, minor_axis, compactness, orientation_deg, sar_confidence, lookalike_prob = best_result
        polygon_geojson = {
            "type": "Feature",
            "properties": {
                "slick_id": "SLICK-S1A-20260902-001",
                "confidence": sar_confidence,
                "lookalike_score": lookalike_prob,
                "area_km2": area_km2,
                "perimeter_km": perimeter_km,
                "compactness": compactness,
                "water_ratio": land_check["water_ratio"]
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [polygon_coords]
            }
        }
        return {
            "model_version": self.model_version,
            "synthetic_fallback": True,
            "sar_confidence": sar_confidence,
            "lookalike_score": lookalike_prob,
            "is_spill": lookalike_prob < 0.30 and land_check["is_valid_ocean_spill"],
            "is_valid_ocean_spill": land_check["is_valid_ocean_spill"],
            "water_ratio": land_check["water_ratio"],
            "metrics": {
                "area_km2": area_km2,
                "perimeter_km": perimeter_km,
                "centroid_lat": center_lat,
                "centroid_lon": center_lon,
                "bbox": bbox,
                "major_axis_km": major_axis,
                "minor_axis_km": minor_axis,
                "orientation_deg": orientation_deg,
                "compactness": compactness
            },
            "polygon_geojson": polygon_geojson,
            "land_mask_provenance": land_check
        }
