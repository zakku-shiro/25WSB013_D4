import cv2
import time
import queue
import os
import dotenv
from vision.camera import Camera
from vision.detector import detect_led
from config.settings import DEBUG_VIEW

dotenv.load_dotenv()
IS_RUNNING_ON_PI = bool(int(os.getenv("IS_RUNNING_ON_PI")))


def vision_process(init_event, mode_settings, vision_q):
    cam = Camera(IS_RUNNING_ON_PI)

    init_event.wait()

    # In sound mode detection is ignored - skip it to reduce CPU load on the Pi
    sound_mode = mode_settings.get('demo_enabled') and mode_settings.get('demo_type')

    prev_time = time.time()

    while True:
        frame = cam.capture_frame()

        result = None if sound_mode else detect_led(frame)

        now = time.time()
        fps = 1 / (now - prev_time)
        prev_time = now

        if result:
            cx = int(result["x"])
            cy = int(result["y"])

            cv2.circle(frame, (cx, cy), 8, (0, 255, 0), 2)
            cv2.putText(frame, f"X:{cx} Err:{int(result['error_x'])}",
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            try:
                while True:
                    vision_q.get_nowait()
            except queue.Empty:
                vision_q.put(result)
        else:
            cv2.putText(frame, "NO TARGET",
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.putText(frame, f"FPS: {int(fps)}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

        cv2.putText(frame,
                    f"Demo: Enabled? {'Yes' if mode_settings['demo_enabled'] else 'No'}, "
                    f"Mode? {'Sound' if mode_settings['demo_type'] else 'Vision'}",
                    (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

        if DEBUG_VIEW:
            cv2.imshow("Robot Vision", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        time.sleep(0.01)

    cam.release()
    cv2.destroyAllWindows()