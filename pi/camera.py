import cv2

class Camera:
    def __init__(self, is_running_on_pi):
        self.FRAME_WIDTH = None
        self.FRAME_HEIGHT = None
        self.TARGET_FPS = None
        self.camera = None

        self.IS_RUNNING_ON_PI = is_running_on_pi

        if is_running_on_pi:
            self.setup_pi_camera()
        else:
            self.setup_windows_camera()

    def setup_pi_camera(self):
        from picamera2 import Picamera2

        self.FRAME_WIDTH = 320
        self.FRAME_HEIGHT = 240
        # self.TARGET_FPS = 10

        self.camera = Picamera2()
        # camera_config = self.camera.create_preview_configuration(main={
        #     "size": (self.FRAME_WIDTH, self.FRAME_HEIGHT),
        #     "format": "RGB888"
        # })
        # self.camera.configure(camera_config)
        # self.camera.set_controls({"FrameRate": self.TARGET_FPS})
        config = self.camera.create_preview_configuration(
            main={"size": (320, 240), "format": "RGB888"},
            controls={
                "FrameRate": 30,
                "ExposureTime": 10000,  # in microseconds
                "AnalogueGain": 1.0
            }
        )
        self.camera.configure(config)
        self.camera.start()

    def setup_windows_camera(self):
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            print("Could not open webcam.")
            exit(1)
        self.FRAME_WIDTH = 320
        self.FRAME_HEIGHT = 240
        # self.TARGET_FPS = int(self.camera.get(cv2.CAP_PROP_FPS))
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.FRAME_WIDTH)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.FRAME_HEIGHT)
        # self.camera.set(cv2.CAP_PROP_FPS, self.TARGET_FPS)

        # Prevent auto-exposure
        self.camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
        self.camera.set(cv2.CAP_PROP_EXPOSURE, -6)

    def capture_frame(self):
        if self.IS_RUNNING_ON_PI:
            return self.camera.capture_array()
        else:
            has_captured, frame = self.camera.read()
            if not has_captured:
                print("Failed to capture frame.")
                exit(1)
            return frame

    def release(self):
        if self.IS_RUNNING_ON_PI:
            self.camera.stop()
        else:
            self.camera.release()