class PID:
    def __init__(self, kp, ki, kd):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.prev_error = 0
        self.integral = 0

    def update(self, error, dt):
        self.integral += error * dt
        derivative = (error - self.prev_error) / dt if dt > 0 else 0

        self.prev_error = error

        return (
            self.kp * error +
            self.ki * self.integral +
            self.kd * derivative
        )
    
    def reset(self):
        self.integral = 0
        self.prev_error = 0
