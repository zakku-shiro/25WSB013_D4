int E1 = 6;
int E2 = 5;
int M1 = 8;
int M2 = 7;

const int trigPin = 9;
const int echoPin = 10;

// Tunables
const int SWEEP_PWM = 90;
const unsigned long SWEEP_MS_180 = 5500;
const unsigned long SAMPLE_PERIOD_MS = 50;

void setup() {
  pinMode(E1, OUTPUT);
  pinMode(E2, OUTPUT);
  pinMode(M1, OUTPUT);
  pinMode(M2, OUTPUT);

  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  digitalWrite(trigPin, LOW);

  Serial.begin(9600);
  delay(200);

  // CSV header
  Serial.println("time_ms,distance_cm");
}

void loop() {
  smoothSweep180WithLogging();
  stopCoast();

  while(true) {} // run once
}

void smoothSweep180WithLogging() {

  unsigned long start = millis();
  unsigned long nextSample = start;

  setLeftTurnDirection();

  analogWrite(E1, SWEEP_PWM);
  analogWrite(E2, SWEEP_PWM);

  while (true) {

    unsigned long now = millis();
    unsigned long elapsed = now - start;

    if (elapsed >= SWEEP_MS_180) break;

    if (now >= nextSample) {

      long distance = getDistanceCm();

      Serial.print(elapsed);
      Serial.print(",");
      Serial.println(distance);

      nextSample += SAMPLE_PERIOD_MS;
    }
  }

  stopBrake();
}

void setLeftTurnDirection() {
  digitalWrite(M1, HIGH);
  digitalWrite(M2, LOW);
}

void stopCoast() {
  analogWrite(E1, 0);
  analogWrite(E2, 0);
}

void stopBrake() {
  analogWrite(E1, 0);
  analogWrite(E2, 0);
  delay(60);
}

// Ultrasonic measurement
long getDistanceCm() {

  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  unsigned long duration = pulseIn(echoPin, HIGH, 30000);

  if (duration == 0) return 0;

  return duration / 58.2;
}