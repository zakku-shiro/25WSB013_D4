import queue
import time
from collections import deque
from control.pid import PID
from control.state_machine import RobotState
from config.settings import *
from utils.math_utils import lerp
from gpio.gpio_rpi import ServoController


def controller_process(ultrasonic_q, vision_q, motor_q, sound_q):
    state = RobotState.SEARCH_SPIN
    pid = PID(KP, KI, KD)

    last_data = None
    last_seen = time.time()
    last_direction = 1
    last_print = 0
    last_update = time.time()
    left = 0
    right = 0

    servo_state = 0
    servo = ServoController()
    last_servo_update = time.time()

    us_distance_queue = deque(maxlen=DISTANCE_QUEUE_SIZE)
    smoothed_distance = None
    last_valid = None
    us_hits = 0
    last_us_hit_time = 0
    verify_start = 0
    verify_hits = 0

    def process_ultrasonic(raw):
        nonlocal last_valid, smoothed_distance

        if raw == 0 or raw > 200:
            return None

        # A large jump indicates a genuine environmental change rather than noise,
        # so reset filter state and accept the new reading as a clean baseline.
        if last_valid is not None and abs(raw - last_valid) > US_JUMP_THRESHOLD:
            us_distance_queue.clear()
            smoothed_distance = None
            last_valid = None

        last_valid = raw
        us_distance_queue.append(raw)

        median = sorted(us_distance_queue)[len(us_distance_queue) // 2]

        if smoothed_distance is None:
            smoothed_distance = median
        else:
            smoothed_distance = lerp(smoothed_distance, median, DISTANCE_SMOOTHING_ALPHA)

        return smoothed_distance

    def transition(new_state):
        nonlocal state, last_servo_update
        if new_state == state:
            return
        print(f"[CTRL] {state.name} -> {new_state.name}")
        if new_state in (RobotState.TRACK, RobotState.SEARCH_SPIN, RobotState.SEARCH_CAMERA):
            pid.reset()
        if new_state == RobotState.SEARCH_CAMERA:
            last_servo_update = time.time()
        state = new_state

    while True:
        now = time.time()
        dt = now - last_update
        last_update = now

        # --- Ultrasonic ---
        try:
            raw = ultrasonic_q.get_nowait()
        except queue.Empty:
            raw = None

        if raw is not None:
            distance = process_ultrasonic(raw)

            if distance is not None:
                if len(us_distance_queue) >= 3:
                    variation = max(us_distance_queue) - min(us_distance_queue)
                else:
                    variation = 999

                if US_CLOSE_MIN < distance < US_CLOSE_MAX and variation < STABILITY_THRESHOLD:
                    us_hits = min(us_hits + 1, US_HITS_REQUIRED * 2)
                    last_us_hit_time = now
                else:
                    us_hits = max(0, us_hits - 1)

        if us_hits > 0 and now - last_us_hit_time > US_TIMEOUT:
            us_hits = 0

        # --- Vision ---
        # Cache the last valid detection so the control loop runs continuously
        # between vision frames rather than stopping on every empty queue poll.
        try:
            last_data = vision_q.get_nowait()
            last_seen = now
        except queue.Empty:
            pass

        target_visible = last_data is not None and (now - last_seen) < LOST_TIMEOUT

        if target_visible:
            data = last_data
            error = data["error_x"]
            area = data["area"]
            last_direction = 1 if error > 0 else -1
        else:
            data = None
            error = None
            area = 0

        # --- State Transitions ---

        # Don't abandon APPROACH on vision loss if the US confirms the target is still ahead.
        # The camera housing commonly obstructs view at close range during approach.
        if not target_visible and now - last_seen > LOST_TIMEOUT:
            if state == RobotState.APPROACH and smoothed_distance is not None and smoothed_distance < APPROACH_DISTANCE:
                pass  # trust the ultrasonic and keep approaching
            elif state not in (RobotState.SEARCH_SPIN, RobotState.SEARCH_CAMERA,
                               RobotState.VERIFY, RobotState.ULTRASONIC):
                transition(RobotState.SEARCH_CAMERA)

        if target_visible and state in (RobotState.SEARCH_CAMERA, RobotState.SEARCH_SPIN):
            transition(RobotState.TRACK)

        if state == RobotState.TRACK and smoothed_distance is not None and smoothed_distance < APPROACH_DISTANCE:
            transition(RobotState.APPROACH)

        if state == RobotState.APPROACH and (smoothed_distance is None or smoothed_distance > APPROACH_DISTANCE * 1.2):
            transition(RobotState.TRACK)

        # At very close range the camera housing obstructs the view, so drive
        # purely off the ultrasonic reading rather than requiring vision confirmation.
        if smoothed_distance is not None and smoothed_distance < US_STOP_DISTANCE:
            if state != RobotState.ULTRASONIC:
                transition(RobotState.ULTRASONIC)
                left, right = 0, 0
                motor_q.put({"left": 0, "right": 0})

        # Mid-range: require vision area confirmation before committing to a stop
        # to avoid halting for incidental obstacles.
        elif us_hits >= US_HITS_REQUIRED and state in (RobotState.TRACK, RobotState.APPROACH,
                                                        RobotState.SEARCH_CAMERA):
            transition(RobotState.VERIFY)
            verify_start = now
            verify_hits = 0

        if state == RobotState.VERIFY:
            if data and area > AREA_THRESHOLD:
                verify_hits += 1
                if verify_hits >= VERIFY_MIN_HITS:
                    transition(RobotState.ULTRASONIC)
            elif now - verify_start > VERIFY_TIMEOUT:
                transition(RobotState.TRACK)

        # Release when distance clears the hysteresis band - no hit timer dependency
        # since entry may have been triggered by distance alone with no hit accumulation.
        if state == RobotState.ULTRASONIC:
            obstruction_cleared = (
                smoothed_distance is None or
                smoothed_distance > US_STOP_DISTANCE * 1.5
            )
            if obstruction_cleared:
                us_hits = 0
                transition(RobotState.TRACK if target_visible else RobotState.SEARCH_CAMERA)

        if state == RobotState.SEARCH_CAMERA and now - last_servo_update > SERVO_SWEEP_INTERVAL:
            if servo_state == 0:
                servo.set_pos(0)
                servo_state = 1
            elif servo_state == 1:
                servo.set_pos(100)
                servo_state = 2
            else:
                servo.set_pos(50)
                servo_state = 0
                transition(RobotState.SEARCH_SPIN)
            last_servo_update = now

        # --- Motor Output ---
        if state == RobotState.SEARCH_SPIN:
            left = 0.75 * BASE_SPEED * last_direction
            right = 0.75 * -BASE_SPEED * last_direction

        elif state in (RobotState.TRACK, RobotState.APPROACH) and target_visible:
            speed = BASE_SPEED if state == RobotState.TRACK else APPROACH_SPEED
            turn_raw = pid.update(error, dt)

            # Soften correction within the deadband to reduce oscillation around centre
            if abs(error) < TRACK_DEADBAND:
                turn_raw *= 0.2

            max_turn = speed * 0.8
            turn_raw = max(-max_turn, min(max_turn, turn_raw))

            # Reduce forward speed when significantly off-axis to tighten turns
            if abs(error) > FRAME_WIDTH / 3:
                speed *= 0.3

            left = speed + turn_raw
            right = speed - turn_raw

            # Friction compensation - ensure motors receive enough voltage to actually move
            if 0 < abs(left) < MIN_MOVE:
                left = MIN_MOVE if left > 0 else -MIN_MOVE
            if 0 < abs(right) < MIN_MOVE:
                right = MIN_MOVE if right > 0 else -MIN_MOVE

        elif state == RobotState.APPROACH and not target_visible:
            left, right = APPROACH_SPEED, APPROACH_SPEED

        elif state == RobotState.TRACK and not target_visible:
            left, right = 0, 0

        elif state in (RobotState.ULTRASONIC, RobotState.VERIFY, RobotState.SEARCH_CAMERA):
            left, right = 0, 0

        # Drain stale commands before pushing the latest to avoid queue back-pressure
        try:
            while True:
                motor_q.get_nowait()
        except queue.Empty:
            pass

        motor_q.put({
            "left": int(left),
            "right": int(right)
        })

        if now - last_print > 0.2:
            dist_str = f"{smoothed_distance:.1f}cm" if smoothed_distance else "---"
            print(
                f"[CTRL] {state.name} | "
                f"L:{int(left)} R:{int(right)} | "
                f"US:{dist_str} hits:{us_hits} | "
                f"area:{int(area)}"
            )
            last_print = now
