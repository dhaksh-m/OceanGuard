from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import torch
import segmentation_models_pytorch as smp


# -------------------------------------------------------------------
# Model configuration
# -------------------------------------------------------------------

MODEL_PATH = (
    Path(__file__).resolve().parent
    / "models"
    / "best_sar_model.pth"
)

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

SAR_INPUT_SIZE = 512
NUM_CLASSES = 5

SEA_CLASS = 0
OIL_CLASS = 1
LOOKALIKE_CLASS = 2
SHIP_CLASS = 3
LAND_CLASS = 4


class OilSpillUNetPredictor:
    """
    Real POSEatSea U-Net + MiT-B2 inference engine.

    Classes:
        0 = Sea Surface
        1 = Oil Spill
        2 = Look-alike
        3 = Ship
        4 = Land
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
    ):
        self.model_path = Path(model_path) if model_path else MODEL_PATH
        self.device = DEVICE

        print(f"Loading SAR model from: {self.model_path}")
        print(f"Using device: {self.device}")

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"SAR model checkpoint not found: {self.model_path}"
            )

        # Build exactly the same architecture as POSEatSea.
        self.model = smp.Unet(
            encoder_name="mit_b2",
            encoder_weights=None,
            in_channels=3,
            classes=NUM_CLASSES,
        )

        # Load trained weights.
        state = torch.load(
            self.model_path,
            map_location=self.device,
            weights_only=True,
        )

        self.model.load_state_dict(
            state,
            strict=True,
        )

        self.model.to(self.device)
        self.model.eval()

        print("SAR U-Net model loaded successfully.")

    # ----------------------------------------------------------------
    # Image preprocessing
    # ----------------------------------------------------------------

    def preprocess(
        self,
        image: np.ndarray,
    ) -> torch.Tensor:
        """
        Convert an RGB image into the input format expected
        by the trained model.
        """

        resized = cv2.resize(
            image,
            (
                SAR_INPUT_SIZE,
                SAR_INPUT_SIZE,
            ),
            interpolation=cv2.INTER_LINEAR,
        )

        arr = resized.astype(
            np.float32
        ) / 255.0

        # HWC -> CHW
        arr = np.transpose(
            arr,
            (2, 0, 1),
        )

        tensor = torch.from_numpy(
            arr
        ).unsqueeze(0)

        return tensor.to(
            self.device
        )

    # ----------------------------------------------------------------
    # Image loading
    # ----------------------------------------------------------------

    def read_image(
        self,
        image_path: str,
    ) -> np.ndarray:
        """
        Read JPG/PNG SAR image and convert BGR -> RGB.
        """

        image = cv2.imread(
            str(image_path),
            cv2.IMREAD_COLOR,
        )

        if image is None:
            raise ValueError(
                f"Could not read SAR image: {image_path}"
            )

        return cv2.cvtColor(
            image,
            cv2.COLOR_BGR2RGB,
        )

    # ----------------------------------------------------------------
    # Prediction
    # ----------------------------------------------------------------

    def predict_mask(
        self,
        sar_image_data: Optional[np.ndarray] = None,
        sar_image_path: Optional[str] = None,
        bbox: Optional[list] = None,
    ) -> dict:
        """
        Run real U-Net inference.

        Either sar_image_data or sar_image_path
        must be provided.
        """

        if (
            sar_image_data is None
            and sar_image_path is None
        ):
            raise ValueError(
                "SAR image data or SAR image path must be provided."
            )

        # Load image if a path was supplied.
        if sar_image_data is None:
            sar_image_data = self.read_image(
                sar_image_path
            )

        if sar_image_data.ndim != 3:
            raise ValueError(
                "SAR image must have shape H x W x C."
            )

        if sar_image_data.shape[2] != 3:
            raise ValueError(
                "SAR image must have 3 channels."
            )

        original_height, original_width = (
            sar_image_data.shape[:2]
        )

        # ------------------------------------------------------------
        # Preprocess
        # ------------------------------------------------------------

        tensor = self.preprocess(
            sar_image_data
        )

        # ------------------------------------------------------------
        # Model inference
        # ------------------------------------------------------------

        with torch.no_grad():

            logits = self.model(
                tensor
            )

            probabilities = torch.softmax(
                logits,
                dim=1,
            )

            prediction = torch.argmax(
                probabilities,
                dim=1,
            )

        # Convert prediction to NumPy.
        mask_512 = (
            prediction
            .squeeze(0)
            .cpu()
            .numpy()
            .astype(np.uint8)
        )

        probabilities_np = (
            probabilities
            .squeeze(0)
            .cpu()
            .numpy()
        )

        # ------------------------------------------------------------
        # Oil probability
        # ------------------------------------------------------------

        oil_probability = probabilities_np[
            OIL_CLASS
        ]

        # Resize prediction back to original image dimensions.
        mask = cv2.resize(
            mask_512,
            (
                original_width,
                original_height,
            ),
            interpolation=cv2.INTER_NEAREST,
        )

        oil_mask = (
            mask == OIL_CLASS
        ).astype(np.uint8)

        # ------------------------------------------------------------
        # Calculate oil metrics
        # ------------------------------------------------------------

        oil_pixels = int(
            np.sum(oil_mask)
        )

        total_pixels = int(
            oil_mask.size
        )

        oil_fraction = (
            oil_pixels / total_pixels
            if total_pixels > 0
            else 0.0
        )

        # Mean probability over pixels classified as oil.
        if oil_pixels > 0:

            oil_mask_512 = cv2.resize(
                oil_mask,
                (
                    SAR_INPUT_SIZE,
                    SAR_INPUT_SIZE,
                ),
                interpolation=cv2.INTER_NEAREST,
            ).astype(bool)

            oil_confidence = float(
                np.mean(
                    oil_probability[
                        oil_mask_512
                    ]
                )
            )

        else:
            oil_confidence = 0.0

        # ------------------------------------------------------------
        # Look-alike fraction
        # ------------------------------------------------------------

        lookalike_pixels = int(
            np.sum(
                mask == LOOKALIKE_CLASS
            )
        )

        lookalike_fraction = (
            lookalike_pixels / total_pixels
            if total_pixels > 0
            else 0.0
        )

        # ------------------------------------------------------------
        # Geometry
        # ------------------------------------------------------------

        # Assumption:
        # Sentinel-1 pixel resolution ~= 10 meters.
        area_km2 = (
            oil_pixels
            * (10.0 * 10.0)
            / 1_000_000.0
        )

        contours, _ = cv2.findContours(
            oil_mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        perimeter_pixels = 0.0

        if contours:

            largest_contour = max(
                contours,
                key=cv2.contourArea,
            )

            perimeter_pixels = float(
                cv2.arcLength(
                    largest_contour,
                    True,
                )
            )

            contour_area = cv2.contourArea(
                largest_contour
            )

        else:

            largest_contour = None
            contour_area = 0.0

        perimeter_km = (
            perimeter_pixels
            * 10.0
            / 1000.0
        )

        # ------------------------------------------------------------
        # Bounding box + actual oil centroid
        # ------------------------------------------------------------

        if bbox is None:

            bbox = [
                103.81,
                1.22,
                103.95,
                1.34,
            ]

        min_lon, min_lat, max_lon, max_lat = bbox

        # Calculate centroid from the actual detected
        # oil pixels rather than the center of the scene.
        moments = cv2.moments(
            oil_mask,
            binaryImage=True,
        )

        if moments["m00"] > 0:

            centroid_x = (
                moments["m10"]
                / moments["m00"]
            )

            centroid_y = (
                moments["m01"]
                / moments["m00"]
            )

            # Convert image X coordinate -> longitude.
            center_lon = (
                min_lon
                + (
                    centroid_x
                    / max(
                        original_width - 1,
                        1,
                    )
                )
                * (
                    max_lon - min_lon
                )
            )

            # Convert image Y coordinate -> latitude.
            # Image Y increases downward,
            # so latitude is inverted.
            center_lat = (
                max_lat
                - (
                    centroid_y
                    / max(
                        original_height - 1,
                        1,
                    )
                )
                * (
                    max_lat - min_lat
                )
            )

        else:

            # Fallback if no oil pixels are detected.
            center_lon = (
                min_lon + max_lon
            ) / 2.0

            center_lat = (
                min_lat + max_lat
            ) / 2.0

        # ------------------------------------------------------------
        # Polygon
        # ------------------------------------------------------------

        polygon_geojson = (
            self._mask_to_geojson(
                oil_mask,
                bbox,
                center_lat,
                center_lon,
            )
        )

        # ------------------------------------------------------------
        # Final result
        # ------------------------------------------------------------

        is_spill = oil_pixels > 0

        return {

            "model_version":
                "poseatsea-unet-mit-b2",

            "sar_confidence": round(
                oil_confidence,
                4,
            ),

            "lookalike_score": round(
                lookalike_fraction,
                4,
            ),

            "is_spill": is_spill,

            "metrics": {

                "area_km2": round(
                    area_km2,
                    4,
                ),

                "perimeter_km": round(
                    perimeter_km,
                    4,
                ),

                "centroid_lat":
                    center_lat,

                "centroid_lon":
                    center_lon,

                "bbox":
                    bbox,

                "major_axis_km":
                    0.0,

                "minor_axis_km":
                    0.0,

                "orientation_deg":
                    0.0,

                "compactness": (
                    float(
                        (
                            4
                            * np.pi
                            * contour_area
                        )
                        / (
                            perimeter_pixels
                            ** 2
                        )
                    )
                    if perimeter_pixels > 0
                    else 0.0
                ),
            },

            "polygon_geojson":
                polygon_geojson,

            # Return the complete class mask
            # so the backend can save it.
            "mask":
                mask,
        }

    # ----------------------------------------------------------------
    # Convert mask -> GeoJSON
    # ----------------------------------------------------------------

    def _mask_to_geojson(
        self,
        oil_mask: np.ndarray,
        bbox: list,
        center_lat: float,
        center_lon: float,
    ) -> dict:

        min_lon, min_lat, max_lon, max_lat = bbox

        contours, _ = cv2.findContours(
            oil_mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        if not contours:

            return {
                "type": "Feature",

                "properties": {
                    "class": "oil_spill",
                },

                "geometry": {
                    "type": "Polygon",
                    "coordinates": [],
                },
            }

        # Select largest detected oil region.
        largest = max(
            contours,
            key=cv2.contourArea,
        )

        polygon = []

        height, width = oil_mask.shape

        # Convert image pixels -> geographic coordinates.
        for point in largest:

            x, y = point[0]

            lon = (
                min_lon
                + (
                    x
                    / max(
                        width - 1,
                        1,
                    )
                )
                * (
                    max_lon - min_lon
                )
            )

            lat = (
                max_lat
                - (
                    y
                    / max(
                        height - 1,
                        1,
                    )
                )
                * (
                    max_lat - min_lat
                )
            )

            polygon.append(
                [
                    round(
                        float(lon),
                        6,
                    ),
                    round(
                        float(lat),
                        6,
                    ),
                ]
            )

        # Close polygon.
        if len(polygon) >= 3:

            polygon.append(
                polygon[0]
            )

        return {

            "type": "Feature",

            "properties": {
                "class": "oil_spill",
                "center_lat": center_lat,
                "center_lon": center_lon,
            },

            "geometry": {

                "type": "Polygon",

                "coordinates": [
                    polygon
                ],
            },
        }

    # ----------------------------------------------------------------
    # Save predicted mask
    # ----------------------------------------------------------------

    def save_mask(
        self,
        mask: np.ndarray,
        output_path: str,
    ):
        """
        Save the predicted class mask to disk.

        Mask values:

            0 = Sea Surface
            1 = Oil Spill
            2 = Look-alike
            3 = Ship
            4 = Land
        """

        output_path = Path(
            output_path
        )

        # Create parent directories if they don't exist.
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        # Save class IDs directly.
        # TIFF is used because the backend expects mask.tif.
        success = cv2.imwrite(
            str(output_path),
            mask.astype(np.uint8),
        )

        if not success:

            raise RuntimeError(
                f"Failed to save mask: {output_path}"
            )

        return str(output_path)