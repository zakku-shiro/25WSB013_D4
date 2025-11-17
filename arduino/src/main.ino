#define PIN_MOTOR_1_SPEED 0x06  // ANALOGUE,  0-255,    Left Motor Speed Control
#define PIN_MOTOR_1_DIRECTION \
  0x08  // DIGITAL,   LOW/HIGH, Left Motor Direction Control
#define PIN_MOTOR_2_SPEED \
  0x05  // ANALOGUE,  0-255,    Right Motor Speed Control
#define PIN_MOTOR_2_DIRECTION \
  0x07  // DIGITAL, LOW/HIGH, Right Motor Direction Control
#define MOTOR_FORWARD LOW
#define MOTOR_REVERSE HIGH
#define MOTOR_OFF_SPEED 0
#define MOTOR_MIN_SPEED 1
#define MOTOR_HALF_SPEED 127
#define MOTOR_MAX_SPEED 255

#include <Arduino.h>
#include <pins_arduino.h>
#include <stddef.h>

void setLeftMotorSpeed(uint8_t motor_speed) {
  Serial.print("Set Left Motor Speed: ");
  Serial.println(motor_speed);
  analogWrite(PIN_MOTOR_1_SPEED, motor_speed);
}

void setRightMotorSpeed(uint8_t motor_speed) {
  Serial.print("Set Right Motor Speed: ");
  Serial.println(motor_speed);
  analogWrite(PIN_MOTOR_2_SPEED, motor_speed);
}

void setMotorSpeed(uint8_t motor_speed) {
  setLeftMotorSpeed(motor_speed);
  setRightMotorSpeed(motor_speed);
}

void moveForward() {
  Serial.println("Change Direction: Forward");
  // Set both motors forward
  digitalWrite(PIN_MOTOR_1_DIRECTION, MOTOR_FORWARD);
  digitalWrite(PIN_MOTOR_2_DIRECTION, MOTOR_FORWARD);
}

void moveForward(size_t delay_ms) {
  moveForward();
  delay(delay_ms);
}

void moveReverse() {
  Serial.println("Change Direction: Reverse");
  // Set both motors in reverse
  digitalWrite(PIN_MOTOR_1_DIRECTION, MOTOR_REVERSE);
  digitalWrite(PIN_MOTOR_2_DIRECTION, MOTOR_REVERSE);
}

void moveReverse(size_t delay_ms) {
  moveReverse();
  delay(delay_ms);
}

void turnLeft() {
  Serial.println("Change Direction: Left");
  // Set motor directions
  digitalWrite(PIN_MOTOR_1_DIRECTION, MOTOR_REVERSE);
  digitalWrite(PIN_MOTOR_2_DIRECTION, MOTOR_FORWARD);
}

void turnLeft(size_t delay_ms) {
  turnLeft();
  delay(delay_ms);
}

void turnRight() {
  Serial.println("Change Direction: Right");
  // Set motor directions
  digitalWrite(PIN_MOTOR_1_DIRECTION, MOTOR_FORWARD);
  digitalWrite(PIN_MOTOR_2_DIRECTION, MOTOR_REVERSE);
}

void turnRight(size_t delay_ms) {
  turnRight();
  delay(delay_ms);
}

void stopMotors() {
  Serial.println("Stopped!");
  analogWrite(PIN_MOTOR_1_SPEED, MOTOR_OFF_SPEED);
  analogWrite(PIN_MOTOR_2_SPEED, MOTOR_OFF_SPEED);
}

void setup() {
  Serial.begin(9600);
  Serial.println("Serial Initialized");
  // GPIO Setup
  for (uint8_t i = 5; i <= 8; i++) {
    Serial.print("Set Pin #");
    Serial.print(i);
    Serial.println(": OUTPUT");
    pinMode(i, OUTPUT);
  }
  Serial.println("GPIO Initialized");

  setMotorSpeed(MOTOR_MAX_SPEED);
}

void loop() {
  turnRight(4000);
  turnLeft(4000);
  moveForward(1000);
  turnRight(1000);
  moveForward(5000);
  turnRight(1000);
  moveForward(5000);
  turnRight(1000);
  moveForward(10000);
  turnRight(1000);
  moveForward(5000);
  turnRight(1000);
  moveForward(5000);
  turnRight(1000);
  moveForward(1000);
  turnRight(2000);
}