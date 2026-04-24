from enum import Enum

class RobotState(Enum):
    SEARCH_CAMERA = 0
    SEARCH_SPIN = 1
    TRACK = 2
    APPROACH = 3
    ULTRASONIC = 4
    VERIFY = 5
