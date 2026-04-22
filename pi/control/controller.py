import queue
import time
from control.pid import PID
from control.state_machine import RobotState
from config.settings import *
from utils.math_utils import apply_deadband, lerp
from gpio.gpio_rpi import ServoController
from collections import deque

def controller_process(ultrasonic_q, vision_q, motor_q, sound_q):
    state = RobotState.SEARCH_SPIN
    pid = PID(KP, KI, KD)

    last_seen = time.time()
    last_direction = 1
    last_print = 0

    left = 0
    right = 0

    servo_state = 0
    servo = ServoController()
    last_servo_update = time.time()

    us_distance_queue = deque(maxlen=DISTANCE_QUEUE_SIZE)
    smoothed_distance = None
    last_valid = None

    def process_ultrasonic(raw):
        nonlocal last_valid, smoothed_distance, us_distance_queue
        if raw == 0 or raw > 200:
            return None

        # Reject sudden jumps
        if last_valid is not None and abs(raw - last_valid) > VARIANCE_TOLERANCE:
            return None
        last_valid = raw
        us_distance_queue.append(raw)

        # Median filter
        median = sorted(us_distance_queue)[len(us_distance_queue) // 2]

        # Exponential smoothing
        if smoothed_distance is None:
            smoothed_distance = median
        else:
            smoothed_distance = lerp(smoothed_distance, median, DISTANCE_SMOOTHING_ALPHA)

        return smoothed_distance

    while True:
        try:
            data = ultrasonic_q.get(timeout=0.25)
            distance = process_ultrasonic(data)
            if distance is None:
                continue
                
            print(f"[US] Raw: {data:.2f} | Filtered: {distance:.2f}")
            if 5 < distance < 25:
                state = RobotState.ULTRASONIC
                left = 0
                right = 0
                motor_q.put({
                    "left": int(left),
                    "right": int(right)
                })

        except queue.Empty:
            if state == RobotState.ULTRASONIC:
                state = RobotState.SEARCH_CAMERA


        try:
            data = vision_q.get(timeout=0.1)
            last_seen = time.time()
        except queue.Empty:
            data = None

        if data:
            error = data["error_x"]
            area = data["area"]
            last_direction = 1 if error > 0 else -1

            if state in (RobotState.SEARCH_CAMERA, RobotState.SEARCH_SPIN):
                state = RobotState.TRACK
            
        else:
            if time.time() - last_seen > LOST_TIMEOUT:
                # Try move the camera first
                if state != RobotState.SEARCH_SPIN:
                    state = RobotState.SEARCH_CAMERA
                    left = 0
                    right = 0


        if (state == RobotState.SEARCH_CAMERA) and time.time() - last_servo_update > LOST_TIMEOUT * 2:
            match (servo_state):
                case 0:
                    servo.set_pos(0)
                    servo_state = 1
                case 1:
                    servo.set_pos(100)
                    servo_state = 2
                case 2:
                    servo.set_pos(50)
                    servo_state = 0
                    state = RobotState.SEARCH_SPIN
            last_servo_update = time.time()


        if state == RobotState.SEARCH_SPIN:
            left, right = BASE_SPEED * (last_direction), -BASE_SPEED * (last_direction)

        elif state in (RobotState.TRACK, RobotState.APPROACH):

            speed = BASE_SPEED if state == RobotState.TRACK else APPROACH_SPEED

            turn_raw = pid.update(error, 0.05)

            # Dead zone
            if abs(error) < TRACK_DEADBAND:
                turn_raw = 0

            # Pivot turn if far off course
            if abs(error) > FRAME_WIDTH / 3:
                speed = 0

            # Combine speed + turn
            left = speed + turn_raw
            right = speed - turn_raw

            # Apply friction compensation
            left = apply_deadband(left, MIN_MOVE)
            right = apply_deadband(right, MIN_MOVE)

        motor_q.put({
            "left": int(left),
            "right": int(right)
        })

        if time.time() - last_print > 0.2:
            print(
                f"[CTRL] State: {state.name} | "
                f"L:{int(left)} R:{int(right)}"
            )
            last_print = time.time()
