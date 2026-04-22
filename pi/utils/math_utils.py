import math
import cv2
from config.settings import *

def apply_deadband(value, min_move, max_input=255):
    if abs(value) < 1:
        return 0

    sign = 1 if value > 0 else -1
    value = abs(value)

    norm = min(value / max_input, 1.0)

    output = min_move + norm * (255 - min_move)

    return int(sign * output)

def calc_circularity(c):
    area = cv2.contourArea(c)
    perimeter = cv2.arcLength(c, True)
    if perimeter == 0:
        return 0
    return (4 * math.pi * area) / (perimeter ** 2)

def size_adjusted_circularity(area):
    t = min(area / MAX_AREA, 1.0) 
    return lerp(MIN_CIRCULARITY_FAR, MIN_CIRCULARITY_CLOSE, t)

def lerp(a, b, t):
    return (1 - t) * a + t * b
