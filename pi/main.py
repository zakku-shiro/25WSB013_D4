import os
import cv2
import dotenv
dotenv.load_dotenv()
from filter_gui import FilterGUI
from camera import Camera
import numpy as np
import time

IS_RUNNING_ON_PI = bool(os.getenv("IS_RUNNING_ON_PI"))
IS_VIDEO_OUTPUT_ENABLED = bool(os.getenv("IS_VIDEO_OUTPUT_ENABLED"))

# Pattern Matching Configs
image_led_pattern = cv2.imread(os.getenv("LIGHT_PATTERN_IMAGE_PATH"), cv2.IMREAD_COLOR_BGR)
led_pattern_width = image_led_pattern.shape[1]
led_pattern_height = image_led_pattern.shape[0]

# TODO: investigate IMREAD_COLOR_RGB vs IMREAD_COLOR_BGR
image_board_pattern = cv2.imread(os.getenv("BOARD_PATTERN_IMAGE_PATH"), cv2.IMREAD_COLOR_BGR)
board_pattern_width = image_board_pattern.shape[1]
board_pattern_height = image_board_pattern.shape[0]

LIGHT_PATTERN_CONFIDENCE        = float(os.getenv("LIGHT_PATTERN_CONFIDENCE"))
BOARD_PATTERN_CONFIDENCE        = float(os.getenv("BOARD_PATTERN_CONFIDENCE"))
BOARD_REGION_TOLERANCE          = float(os.getenv("BOARD_REGION_TOLERANCE"))
LAST_SEEN_MOVEMENT_TOLERANCE    = float(os.getenv("LAST_SEEN_MOVEMENT_TOLERANCE"))
STABILITY_COUNTER_MAX           = int(os.getenv("STABILITY_COUNTER_MAX"))

# Camera Initialization Configs
main_camera = Camera(IS_RUNNING_ON_PI)

# Computer Vision Configs
board_filter_gui = FilterGUI("Board Filter", [int(x) for x in os.getenv("BOARD_FILTER_VALUES").split(",")])
light_filter_gui = FilterGUI("Light Filter", [int(x) for x in os.getenv("LIGHT_FILTER_VALUES").split(",")])

def apply_hsv_filter(input_frame_bgr, hsv_filter: FilterGUI):
    image_hsv = cv2.cvtColor(input_frame_bgr, cv2.COLOR_BGR2HSV)

    h, s, v = cv2.split(image_hsv)
    s = apply_hsv_shift(s, hsv_filter.sat_off)
    v = apply_hsv_shift(v, hsv_filter.val_off)
    image_hsv = cv2.merge((h, s, v))

    lower_bounds = np.array([hsv_filter.hue_min, hsv_filter.sat_min, hsv_filter.val_min])
    upper_bounds = np.array([hsv_filter.hue_max, hsv_filter.sat_max, hsv_filter.val_max])
    mask = cv2.inRange(image_hsv, lower_bounds, upper_bounds)
    result = cv2.bitwise_and(image_hsv, image_hsv, mask = mask)

    return cv2.cvtColor(result, cv2.COLOR_HSV2BGR)

def apply_hsv_shift(channel, amount):
    if amount > 0:
        lim = 255 - amount
        channel[channel >= lim] = 255
        channel[channel < lim] += amount
    elif amount < 0:
        amount *= -1
        lim = amount
        channel[channel <= lim] = 0
        channel[channel > lim] -= amount
    return channel

if IS_VIDEO_OUTPUT_ENABLED:
    video_writer = cv2.VideoWriter("output.mp4", cv2.VideoWriter_fourcc(*"MP4V"), main_camera.TARGET_FPS, (main_camera.FRAME_WIDTH, main_camera.FRAME_HEIGHT))
    video_writer_filtered = cv2.VideoWriter("output_filtered.mp4", cv2.VideoWriter_fourcc(*"MP4V"), main_camera.TARGET_FPS, (main_camera.FRAME_WIDTH, main_camera.FRAME_HEIGHT))
else:
    video_writer = None
    video_writer_filtered = None

previous_frame_time = 0
current_frame_time = 0
while True:
    current_frame_time = time.time()
    fps = "FPS: " + str(round(1 / (current_frame_time - previous_frame_time), 2))
    previous_frame_time = current_frame_time
    print(fps)

    frame = main_camera.capture_frame()
    light_filtered_frame = apply_hsv_filter(frame, light_filter_gui)
    board_filtered_frame = apply_hsv_filter(frame, board_filter_gui)

    board_matches = cv2.matchTemplate(board_filtered_frame, image_board_pattern, cv2.TM_CCOEFF_NORMED)
    _, board_best_confidence, _, board_best_location = cv2.minMaxLoc(board_matches)
    if board_best_confidence > BOARD_PATTERN_CONFIDENCE:
        print(f"Board match confidence: {board_best_confidence:.2%}")
        board_top_left = board_best_location
        board_bottom_right = (board_top_left[0] + board_pattern_width, board_top_left[1] + board_pattern_height)
        cv2.rectangle(frame, board_top_left, board_bottom_right, (255, 0, 0), 2)

        # ((x0,y0), (x1,y1))
        light_search_window = ((max(0, int(board_top_left[0] - (board_pattern_width * BOARD_REGION_TOLERANCE))),
                                max(0, int(board_top_left[1] - (board_pattern_height * BOARD_REGION_TOLERANCE)))),
                               (min(main_camera.FRAME_WIDTH, int(board_bottom_right[0] + (board_pattern_width * BOARD_REGION_TOLERANCE))),
                                min(main_camera.FRAME_HEIGHT, int(board_bottom_right[1] + (board_pattern_height * BOARD_REGION_TOLERANCE)))))
        cv2.rectangle(frame, light_search_window[0], light_search_window[1], (0, 165, 255), 2)

        light_matches = cv2.matchTemplate(light_filtered_frame[
                                            board_top_left[1]:(board_top_left[1] + board_pattern_height),
                                            board_top_left[0]:(board_top_left[0] + board_pattern_width),
                                          ], image_led_pattern, cv2.TM_CCOEFF_NORMED)
        _, light_best_confidence, _, light_best_location = cv2.minMaxLoc(light_matches)
        if light_best_confidence > LIGHT_PATTERN_CONFIDENCE:
            print(f"Light match confidence: {light_best_confidence:.2%}")
            light_top_left = (light_search_window[0][0] + light_best_location[0], light_search_window[0][1] + light_best_location[1])
            light_bottom_right = (light_top_left[0] + led_pattern_width, light_top_left[1] + led_pattern_height)
            cv2.rectangle(frame, light_top_left, light_bottom_right, (0, 255, 0), 2)

    cv2.putText(frame, fps, (5, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0),
                2, cv2.LINE_AA)
    cv2.imshow("Board Filtering", board_filtered_frame)
    cv2.imshow("Light Filtering", light_filtered_frame)
    cv2.imshow("Camera View", frame)

    if IS_VIDEO_OUTPUT_ENABLED:
        video_writer.write(frame)
        video_writer_filtered.write(board_filtered_frame)

    if cv2.waitKey(1) == ord("q"):
        break

main_camera.release()
cv2.destroyAllWindows()