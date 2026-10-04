"""Measurable, review-oriented image quality signals."""

import cv2
import numpy as np

from ..core.result import Finding

MIN_DIMENSION = 64
MIN_BLUR_SCORE = 100.0
VERY_DARK_MEAN = 20.0
VERY_BRIGHT_MEAN = 235.0
EXTREME_ASPECT_RATIO = 3.0


def analyze_quality(records: list[dict]) -> tuple[list[dict], list[Finding]]:
    measurements, findings = [], []
    for record in records:
        if not record.get("readable"):
            continue
        path = record["path"]
        image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if image is None:
            continue
        gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape[:2]
        aspect = width / height if height else None
        brightness = float(np.mean(gray))
        blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        values = {"file": path, "width": width, "height": height,
                  "aspect_ratio": round(aspect, 4) if aspect is not None else None,
                  "brightness_mean": round(brightness, 3), "blur_score": round(blur_score, 3)}
        measurements.append(values)
        context = {"file": path, "width": width, "height": height, "measured_value": None}
        if width < MIN_DIMENSION or height < MIN_DIMENSION:
            findings.append(Finding("image_quality", "low_resolution", "medium",
                                    f"Image resolution is small ({width}×{height}).", 2.0,
                                    metadata={**context, "measured_value": min(width, height), "threshold": MIN_DIMENSION}))
        if aspect is not None and (aspect > EXTREME_ASPECT_RATIO or aspect < 1 / EXTREME_ASPECT_RATIO):
            findings.append(Finding("image_quality", "extreme_aspect_ratio", "low",
                                    f"Image has an extreme aspect ratio ({aspect:.2f}:1).", 1.0,
                                    metadata={**context, "measured_value": round(aspect, 4), "threshold": EXTREME_ASPECT_RATIO}))
        if brightness <= VERY_DARK_MEAN or brightness >= VERY_BRIGHT_MEAN:
            kind = "very_dark_image" if brightness <= VERY_DARK_MEAN else "very_bright_image"
            findings.append(Finding("image_quality", "brightness_anomaly", "medium",
                                    f"Image may be {'very dark' if brightness <= VERY_DARK_MEAN else 'very bright'} (mean intensity {brightness:.1f}/255).", 2.0,
                                    metadata={**context, "kind": kind, "measured_value": round(brightness, 3),
                                              "dark_threshold": VERY_DARK_MEAN, "bright_threshold": VERY_BRIGHT_MEAN}))
        if blur_score < MIN_BLUR_SCORE:
            findings.append(Finding("image_quality", "possible_blur", "low",
                                    f"Image may be blurry (Laplacian variance {blur_score:.2f}).", 1.0,
                                    metadata={**context, "measured_value": round(blur_score, 3), "threshold": MIN_BLUR_SCORE,
                                              "method": "variance_of_laplacian"}))
    return measurements, findings
