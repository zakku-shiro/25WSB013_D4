import time
import pigpio
import sys
sys.path.append("..")
from utils.math_utils import lerp


class ServoController:
    SERVO_PIN = 23

    MIN_PW = 600
    MAX_PW = 800

    def __init__(self):
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError(
                "pigpio daemon is not running — start it with: sudo pigpiod"
            )
        self.set_pos(50)

    def set_pos(self, position):
        """
        position: 0–100
        Sends a DMA-timed pulse to the servo then idles the signal to prevent
        holding torque and generating heat when stationary.
        """
        if not (0 <= position <= 100):
            return

        pw = int(lerp(self.MIN_PW, self.MAX_PW, position / 100))
        print(f"Setting servo: {pw}us")
        self.pi.set_servo_pulsewidth(self.SERVO_PIN, pw)
        time.sleep(1.5)
        self.pi.set_servo_pulsewidth(self.SERVO_PIN, 0)
        print("Servo idle")

    def stop(self):
        self.pi.set_servo_pulsewidth(self.SERVO_PIN, 0)
        self.pi.stop()


if __name__ == "__main__":
    servo = ServoController()
    time.sleep(1)
    servo.set_pos(0)
    time.sleep(1)
    servo.set_pos(100)
    time.sleep(1)
    servo.set_pos(50)
    servo.stop()
