import math
import os
import time
import cv2
import dotenv
import numpy as np
from camera import Camera

def calc_circularity(c):
    """Calculates the circularity for reflection filtering."""
    area = cv2.contourArea(c)
    perimeter = cv2.arcLength(c, True)
    if perimeter == 0: return 0
    return (4 * math.pi * area) / (perimeter ** 2)

def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolate on the scale given by a to b, using t as the point on that scale."""
    return (1 - t) * a + t * b

dotenv.load_dotenv()
# ====== Dotenv Configs ======
IS_RUNNING_ON_PI = bool(int(os.getenv("IS_RUNNING_ON_PI")))
IS_VIDEO_OUTPUT_ENABLED = bool(int(os.getenv("IS_VIDEO_OUTPUT_ENABLED")))

FRAME_WIDTH = int(os.getenv("FRAME_WIDTH"))
FRAME_HEIGHT = int(os.getenv("FRAME_HEIGHT"))

MIN_AREA = int(os.getenv("MIN_AREA")) # Minimum LED size
MAX_AREA = int(os.getenv("MAX_AREA")) # Maximum LED size
MIN_CIRCULARITY = float(os.getenv("MIN_CIRCULARITY")) # Reflection filtering
VALUE_MIN = int(os.getenv("VALUE_MIN"))

SMOOTHING_ALPHA = float(os.getenv("SMOOTHING_ALPHA")) # 0->1 responsive & jittery -> floaty & smooth
# ============================

# Camera Initialization Configs
main_camera = Camera(IS_RUNNING_ON_PI)

if IS_VIDEO_OUTPUT_ENABLED:
    video_writer = cv2.VideoWriter("output.mp4", cv2.VideoWriter_fourcc(*"MP4V"), main_camera.TARGET_FPS, (main_camera.FRAME_WIDTH, main_camera.FRAME_HEIGHT))
    video_writer_filtered = cv2.VideoWriter("output_filtered.mp4", cv2.VideoWriter_fourcc(*"MP4V"), main_camera.TARGET_FPS, (main_camera.FRAME_WIDTH, main_camera.FRAME_HEIGHT))
else:
    video_writer = None
    video_writer_filtered = None

previous_frame_time = 0
current_frame_time = 0
smoothed_x = None
smoothed_y = None
while True:
    current_frame_time = time.time()
    fps = "FPS: " + str(round(1 / (current_frame_time - previous_frame_time), 2))
    previous_frame_time = current_frame_time
    print(fps)

    frame = main_camera.capture_frame()

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

    # Erode and Dilate to clean up noise and smoothen edges
    kernel = np.ones((3, 3), np.uint8)
    eroded_frame = cv2.morphologyEx(frame_red_filtered, cv2.MORPH_OPEN, kernel)
    dilated_frame = cv2.morphologyEx(eroded_frame, cv2.MORPH_CLOSE, kernel)

    # Find contours using the inexpensive CHAIN_APPROX_SIMPLE and only returning outer rings for the LED.
    contours, _ = cv2.findContours(
        dilated_frame,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    # Filter for valid contour rings (goldilocks) then find the largest and most circular
    candidates = [
        c for c in contours
        if MIN_AREA < cv2.contourArea(c) < MAX_AREA
           and calc_circularity(c) > MIN_CIRCULARITY
    ]
    best_contour = max(candidates, key = cv2.contourArea, default = None)

    if best_contour is None:
        # We've either lost it or not found it yet, clear values accordingly.
        smoothed_x = None
        smoothed_y = None
    else:   # We have a match.
        print(calc_circularity(best_contour))
        """
        Horrifically cool function that blends physics with computer vision.
        Essentially, m00 is the 'mass' of the 'object' shown in the mask,
        being calculated as the summation or count of all '1' pixels indicating
        red/valid pixels in our mask. This makes m10 and m01 the moments about
        the x and y axis respectively - this distribution representation gives
        us a rough understanding of the centre of the LED.
        """
        matrix_moments = cv2.moments(best_contour)
        if matrix_moments["m00"] != 0:
            cx = int(matrix_moments["m10"] / matrix_moments["m00"])
            cy = int(matrix_moments["m01"] / matrix_moments["m00"])

            if smoothed_x is None:
                # If this is our first detection, just use the central values.
                smoothed_x = cx
                smoothed_y = cy
            else:
                # Otherwise, linearly interpolate across the new and old pos.
                smoothed_x = lerp(smoothed_x, cx, SMOOTHING_ALPHA)
                smoothed_y = lerp(smoothed_y, cy, SMOOTHING_ALPHA)


            # Draw detection circle.
            cv2.circle(frame, (int(smoothed_x), int(smoothed_y)),
                       8, (0,255,0), 2)

            # Calculate the offset from the centre of the frame.
            error_x = smoothed_x - FRAME_WIDTH / 2
            error_y = smoothed_y - FRAME_HEIGHT / 2

            print(f"LED: {int(smoothed_x)}, {int(smoothed_y)} | "
                  f"ErrX: {int(error_x)}")

            # TODO: send serial data here to arduino


    # FPS text
    cv2.putText(frame, fps, (5, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0),
                2, cv2.LINE_AA)

    # Display debugging windows
    cv2.imshow("Camera View", frame)
    cv2.imshow("Masked Frame", dilated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    if IS_VIDEO_OUTPUT_ENABLED:
        video_writer.write(frame)
        video_writer_filtered.write(dilated_frame)

    if cv2.waitKey(1) == ord("q"):
        break

main_camera.release()
cv2.destroyAllWindows()