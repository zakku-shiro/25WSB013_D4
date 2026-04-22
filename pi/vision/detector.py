import cv2
import numpy as np
from config.settings import *
from utils.math_utils import lerp

DETECTOR_VIEW = False

_smoothed_x = None
_smoothed_y = None


def _fill_ratio(contour):
    """
    Ratio of contour area to its minimum enclosing circle area.
    Unlike perimeter-based circularity, this is robust to jagged edges
    on large blobs — only the overall shape extent matters.
    Perfect circle = 1.0, irregular blob = lower.
    """
    _, radius = cv2.minEnclosingCircle(contour)
    if radius == 0:
        return 0
    return cv2.contourArea(contour) / (np.pi * radius ** 2)


def _size_adjusted_threshold(area):
    """
    Relax the shape threshold as the blob grows, normalised against
    the expected maximum LED area at close range rather than MAX_AREA.
    """
    t = min(area / CIRCULARITY_AREA_SCALE, 1.0)
    return lerp(MIN_CIRCULARITY_FAR, MIN_CIRCULARITY_CLOSE, t)


def detect_led(frame):
    global _smoothed_x, _smoothed_y

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Red mask — dual band to handle HSV wrap-around
    lower_red1 = np.array([0,   120, VALUE_MIN])
    upper_red1 = np.array([10,  255, 255])
    lower_red2 = np.array([170, 120, VALUE_MIN])
    upper_red2 = np.array([180, 255, 255])
    mask_red = cv2.inRange(hsv, lower_red1, upper_red1) | \
               cv2.inRange(hsv, lower_red2, upper_red2)

    # White core gating — fills in the blown-out saturated centre.
    # Large dilation kernel ensures the gate reaches inward on big blobs.
    mask_white = cv2.inRange(hsv, np.array([0, 0, 240]), np.array([180, 40, 255]))
    red_dilated = cv2.dilate(mask_red, np.ones((31, 31), np.uint8))
    mask_white_gated = cv2.bitwise_and(mask_white, red_dilated)

    mask_combined = mask_red | mask_white_gated

    # Morphology: open removes noise, close fills the LED blob
    kernel = np.ones((3, 3), np.uint8)
    mask_clean = cv2.morphologyEx(mask_combined, cv2.MORPH_OPEN,  kernel)
    mask_clean = cv2.morphologyEx(mask_clean,    cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(
        mask_clean,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    candidates = [
        c for c in contours
        if MIN_AREA < cv2.contourArea(c) < MAX_AREA
        and _fill_ratio(c) > _size_adjusted_threshold(cv2.contourArea(c))
    ]

    best_contour = max(candidates, key=cv2.contourArea, default=None)

    if best_contour is None:
        _smoothed_x = None
        _smoothed_y = None
        return None

    matrix_moments = cv2.moments(best_contour)
    if matrix_moments["m00"] == 0:
        return None

    cx = int(matrix_moments["m10"] / matrix_moments["m00"])
    cy = int(matrix_moments["m01"] / matrix_moments["m00"])

    if _smoothed_x is None:
        _smoothed_x, _smoothed_y = float(cx), float(cy)
    else:
        _smoothed_x = lerp(_smoothed_x, cx, SMOOTHING_ALPHA)
        _smoothed_y = lerp(_smoothed_y, cy, SMOOTHING_ALPHA)

    error_x = _smoothed_x - FRAME_WIDTH  / 2
    error_y = _smoothed_y - FRAME_HEIGHT / 2

    if DETECTOR_VIEW:
        cv2.circle(mask_clean, (int(_smoothed_x), int(_smoothed_y)), 8, 128, 2)
        cv2.imshow("Detector Vision", mask_clean)

    return {
        "x":       _smoothed_x,
        "y":       _smoothed_y,
        "error_x": error_x,
        "error_y": error_y,
        "area":    cv2.contourArea(best_contour)
    }
