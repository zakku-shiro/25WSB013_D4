import cv2
import numpy as np
from utils.math_utils import calc_circularity
from config.settings import MIN_AREA, MAX_AREA, MIN_CIRCULARITY, FRAME_WIDTH

def detect_led(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    mask1 = cv2.inRange(hsv, (0,120,120), (10,255,255))
    mask2 = cv2.inRange(hsv, (170,120,120), (180,255,255))
    mask = mask1 | mask2

    kernel = np.ones((3,3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    contours,_ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    candidates = [
        c for c in contours
        if MIN_AREA < cv2.contourArea(c) < MAX_AREA
        and calc_circularity(c) > MIN_CIRCULARITY
    ]

    if not candidates:
        return None

    best = max(candidates, key=cv2.contourArea)
    m = cv2.moments(best)

    if m["m00"] == 0:
        return None

    cx = int(m["m10"] / m["m00"])
    cy = int(m["m01"] / m["m00"])

    error_x = cx - FRAME_WIDTH / 2

    return {
        "x": cx,
        "y": cy,
        "error_x": error_x,
        "area": cv2.contourArea(best)
    }

#############################

import os
import cv2
import dotenv
import numpy as np
from config.settings import *
from utils.math_utils import *

DETECTOR_VIEW = False

_smoothed_x = None
_smoothed_y = None

def detect_led(frame):
    global _smoothed_x, _smoothed_y

    # HSV Color Filtering
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # HSV values for red wrap around at the end, hence the upper and lower bands.
    lower_red1 = np.array([0, 120, VALUE_MIN])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 120, VALUE_MIN])
    upper_red2 = np.array([180, 255, 255])

    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    frame_red_filtered = mask1 | mask2

    # Detect blown-out LED core (high value, low saturation = oversaturated centre).
    # Only accept white pixels that are surrounded by red to reject room lights.
    lower_white = np.array([0, 0, 240])
    upper_white = np.array([180, 40, 255])
    mask_white = cv2.inRange(hsv, lower_white, upper_white)
    red_dilated = cv2.dilate(frame_red_filtered, np.ones((15, 15), np.uint8))
    mask_white_gated = cv2.bitwise_and(mask_white, red_dilated)

    # Combine red and gated white into a single mask
    mask_combined = frame_red_filtered | mask_white_gated

    # Erode and dilate to clean up noise and fill the LED blob
    kernel = np.ones((3, 3), np.uint8)
    opened = cv2.morphologyEx(mask_combined, cv2.MORPH_OPEN, kernel)
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)

    # Find contours - inexpensive CHAIN_APPROX_SIMPLE, outer rings only
    contours, _ = cv2.findContours(
        closed,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    # Filter for valid contours (goldilocks area + circularity), take largest
    candidates = [
        c for c in contours
        if MIN_AREA < cv2.contourArea(c) < MAX_AREA
        and calc_circularity(c) > 0.65
    ]
    best_contour = max(candidates, key=cv2.contourArea, default=None)

    if best_contour is None:
        _smoothed_x = None
        _smoothed_y = None
        return None

    """
    Horrifically cool function that blends physics with computer vision.
    Essentially, m00 is the 'mass' of the 'object' shown in the mask,
    being calculated as the summation or count of all '1' pixels indicating
    red/valid pixels in our mask. This makes m10 and m01 the moments about
    the x and y axis respectively - this distribution representation gives
    us a rough understanding of the centre of the LED.
    """
    matrix_moments = cv2.moments(best_contour)
    if matrix_moments["m00"] == 0:
        return None

    cx = int(matrix_moments["m10"] / matrix_moments["m00"])
    cy = int(matrix_moments["m01"] / matrix_moments["m00"])

    if _smoothed_x is None:
        _smoothed_x, _smoothed_y = cx, cy
    else:
        _smoothed_x = lerp(_smoothed_x, cx, SMOOTHING_ALPHA)
        _smoothed_y = lerp(_smoothed_y, cy, SMOOTHING_ALPHA)

    error_x = _smoothed_x - FRAME_WIDTH / 2
    error_y = _smoothed_y - FRAME_HEIGHT / 2

    if DETECTOR_VIEW:
        cv2.circle(closed, (_smoothed_x, _smoothed_y), 8, (0, 255, 255), 2)
        cv2.imshow("Detector Vision", closed)

    return {
        "x": _smoothed_x,
        "y": _smoothed_y,
        "error_x": error_x,
        "error_y": error_y,
        "area": cv2.contourArea(best_contour)
    }

