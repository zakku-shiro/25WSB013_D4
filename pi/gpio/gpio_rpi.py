import RPi.GPIO as gpio
from time import sleep

import sys
sys.path.append("..")
from utils.math_utils import lerp

class ServoController:
    MIN_POSITION = 3.0
    MAX_POSITION = 4.0

    def __init__(self):
        gpio.setwarnings(False)
        gpio.setmode(gpio.BOARD)
        gpio.setup(16, gpio.OUT)

        self.pwm = gpio.PWM(16, 50)
        self.pwm.start(0)
        self.set_pos(50)

    def set_pos(self, position):
        """
            position: (0->100)
        """
        if not (0 <= position <= 100):
            return

        new_duty = lerp(
                self.MIN_POSITION, 
                self.MAX_POSITION,
                position / 100)
        print(f"Setting PWM to {new_duty}")
        self.pwm.ChangeDutyCycle(new_duty)
        sleep(1.5)
        self.pwm.ChangeDutyCycle(0)
        print("Stopping PWM")

if __name__ == "__main__":
    servo = ServoController()
    sleep(1)
    servo.set_pos(0)
    sleep(1)
    servo.set_pos(100)
    sleep(1)
    servo.set_pos(50)
