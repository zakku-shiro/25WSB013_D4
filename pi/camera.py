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

        self.FRAME_WIDTH = 800
        self.FRAME_HEIGHT = 800
        self.TARGET_FPS = 10

        self.camera = Picamera2()
        camera_config = self.camera.create_preview_configuration(main={
            "size": (self.FRAME_WIDTH, self.FRAME_HEIGHT),
            "format": "RGB888"
        })
        self.camera.configure(camera_config)
        self.camera.set_controls({"FrameRate": self.TARGET_FPS})
        self.camera.start()

    def setup_windows_camera(self):
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            print("Could not open webcam.")
            exit(1)
        self.FRAME_WIDTH = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.FRAME_HEIGHT = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.TARGET_FPS = int(self.camera.get(cv2.CAP_PROP_FPS))

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