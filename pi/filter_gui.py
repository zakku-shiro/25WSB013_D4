import cv2

class FilterGUI:
    @property
    def hue_min(self):
        return self._hue_min

    @property
    def hue_max(self):
        return self._hue_max

    @property
    def sat_min(self):
        return self._sat_min

    @property
    def sat_max(self):
        return self._sat_max

    @property
    def val_min(self):
        return self._val_min

    @property
    def val_max(self):
        return self._val_max

    @property
    def sat_off(self):
        return self._sat_off

    @property
    def val_off(self):
        return self._val_off

    def __init__(self, window_name = "HSV Filter Controls", h_min = 0, h_max = 179, sat_min = 0, sat_max = 255, val_min = 0, val_max = 255, sat_off = 0, val_off = 0):
        self.WINDOW_NAME = window_name
        cv2.namedWindow(self.WINDOW_NAME, flags = cv2.WINDOW_AUTOSIZE)

        self._hue_min = h_min
        self._hue_max = h_max
        self._sat_min = sat_min
        self._sat_max = sat_max
        self._val_min = val_min
        self._val_max = val_max
        self._sat_off = sat_off
        self._val_off = val_off

        cv2.createTrackbar("Hue Min", self.WINDOW_NAME, 0, 179, lambda x: setattr(self, "_hue_min", x))
        cv2.createTrackbar("Hue Max", self.WINDOW_NAME, 0, 179, lambda x: setattr(self, "_hue_max", x))
        cv2.createTrackbar("Sat Min", self.WINDOW_NAME, 0, 255, lambda x: setattr(self, "_sat_min", x))
        cv2.createTrackbar("Sat Max", self.WINDOW_NAME, 0, 255, lambda x: setattr(self, "_sat_max", x))
        cv2.createTrackbar("Val Min", self.WINDOW_NAME, 0, 255, lambda x: setattr(self, "_val_min", x))
        cv2.createTrackbar("Val Max", self.WINDOW_NAME, 0, 255, lambda x: setattr(self, "_val_max", x))
        cv2.createTrackbar("Sat Off", self.WINDOW_NAME, 0, 255, lambda x: setattr(self, "_sat_off", x))
        cv2.createTrackbar("Val Off", self.WINDOW_NAME, 0, 255, lambda x: setattr(self, "_val_off", x))

        # Strange minimum value fix
        cv2.setTrackbarMin("Sat Off", self.WINDOW_NAME, -255)
        cv2.setTrackbarMin("Val Off", self.WINDOW_NAME, -255)

        # Set default values
        cv2.setTrackbarPos("Hue Min", self.WINDOW_NAME, h_min)
        cv2.setTrackbarPos("Hue Max", self.WINDOW_NAME, h_max)
        cv2.setTrackbarPos("Sat Min", self.WINDOW_NAME, sat_min)
        cv2.setTrackbarPos("Sat Max", self.WINDOW_NAME, sat_max)
        cv2.setTrackbarPos("Val Min", self.WINDOW_NAME, val_min)
        cv2.setTrackbarPos("Val Max", self.WINDOW_NAME, val_max)
        cv2.setTrackbarPos("Sat Off", self.WINDOW_NAME, sat_off)
        cv2.setTrackbarPos("Val Off", self.WINDOW_NAME, val_off)