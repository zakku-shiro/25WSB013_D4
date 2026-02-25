int E1 = 6;
int E2 = 5;
int M1 = 8;
int M2 = 7;

const int trigPin = 9;
const int echoPin = 10;

// Tunables
const int SWEEP_PWM = 90;                  // adjust 120–200
const unsigned long SWEEP_MS_180 = 5500;    // estimated time of spinning
const unsigned long SWEEP_MS_MAX = 6000;    //prevents multiple spinning 
const unsigned long SAMPLE_PERIOD_MS = 50;

const float DEG_PER_MS = 180.0f / (float)SWEEP_MS_180;

void setup() {
  for (int i = 5; i <= 8; i++) pinMode(i, OUTPUT);

  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  digitalWrite(trigPin, LOW);

  Serial.begin(9600);
  delay(200);

  Serial.println("t_ms,angle_deg_est,distance_cm");
}

void loop() {
  smoothSweep180WithLogging();
  stopCoast(); 
  while (true) { }
}

void smoothSweep180WithLogging() {
  unsigned long start = millis();
  unsigned long nextSample = start;

  setLeftTurnDirection();

  // Start move
  analogWrite(E1, SWEEP_PWM);
  analogWrite(E2, SWEEP_PWM);

  while (true) {
    unsigned long now = millis();
    unsigned long elapsed = now - start;

    // Stop 
    if (elapsed >= SWEEP_MS_180) break;
    if (elapsed >= SWEEP_MS_MAX) break;

    // colelct samp
    if (now >= nextSample) {
      long d = getDistanceCm();
      float angle = elapsed * DEG_PER_MS;

      Serial.print(elapsed);
      Serial.print(",");
      Serial.print(angle, 2);
      Serial.print(",");

      if (d == 0) Serial.println("0");
      else Serial.println(d);

      nextSample += SAMPLE_PERIOD_MS;
    }
  }

  // overshoot prevents 
  stopBrake();
  Serial.println("DONE");
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
  analogWrite(E1, 120);
  digitalWrite(M1, LOW);
  analogWrite(E2, 120);
  digitalWrite(M2, HIGH);
  delay(60);

  stopCoast();
}

//ultra
long getDistanceCm() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  unsigned long duration = pulseIn(echoPin, HIGH, 30000);
  if (duration == 0) return 0;

  return (long)(duration * 0.0343 / 2.0);
}