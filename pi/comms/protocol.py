import enum

class Signals(enum.IntEnum):
    PING = 0
    ERROR = 1
    ACKNOWLEDGE = 2
    SOUND_DATA = 3
    LED_COMMAND = 4
    MOVE_COMMAND = 5
    ULTRASONIC_DATA = 6
    SWITCH_DATA = 7