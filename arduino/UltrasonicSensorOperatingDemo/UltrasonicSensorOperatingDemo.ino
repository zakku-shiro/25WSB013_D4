// Ultrasonic distance demo for robot approach behaviour

const int trigPin = 9;   
const int echoPin = 10;

bool validatedAt30 = false;
bool validatedAt20 = false;

void setup() {
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  digitalWrite(trigPin, LOW);

  Serial.begin(9600);
  Serial.println("Robot approach DEMO");
}

void loop() {
  approachDemo();

  while (true) { }
}


void approachDemo() {
  validatedAt30 = false;
  validatedAt20 = false;

  while (true) {
    long d = getDistanceCm();

    if (d == 0) {
      Serial.println("No valid ultrasonic reading (distance = 0).");
      delay(300);
      continue;
    }

    // 30 cm checkpoint 
    if (!validatedAt30 && d <= 30 && d > 20) {
      Serial.println();
      Serial.println(" CHECKPOINT: ~30 cm reached ");
      Serial.println("Validating direction...");
      delay(1000);
      Serial.println("Direction corrected. Continuing.");
      Serial.println();
      validatedAt30 = true;
    }

    // 20 cm checkpoint
    if (!validatedAt20 && d <= 20 && d > 10) {
      Serial.println();
      Serial.println("CHECKPOINT: ~20 cm reached");
      Serial.println("Validating direction...");
      delay(1000);
      Serial.println("Direction corrected. Continuing.");
      Serial.println();
      validatedAt20 = true;
    }

    //Distance → PWM Speed 
    int pwm = 0;
    const char* mode = "";

    if (d > 50) {
      pwm = 255;    // far away full
      mode = "APPROACH FAST (>50cm)";
    }
    else if (d > 30) {
      pwm = 255;    // full 
      mode = "APPROACH FAST (50–30cm)";
    }
    else if (d > 20) {
      pwm = 255;    //  full
      mode = "APPROACH FAST (30–20cm)";
    }
    else if (d > 10) {
      pwm = 128;    // half speed
      mode = "APPROACH MEDIUM (20–10cm)";
    }
    else if (d > 5) {
      pwm = 64;     // slow creep
      mode = "APPROACH SLOW (10–5cm)";
    }
    else {
      pwm = 0;      // stop
      mode = "TARGET REACHED";
    }

    //If at target distance 
    if (pwm == 0) {
      Serial.println();
      Serial.print("Distance: ");
      Serial.print(d);
      Serial.println(" cm");
      Serial.println("PWM Speed: 0");
      Serial.println("Mode: TARGET REACHED");
      Serial.println("Distance has been met, all motors off, source detected.");
      break;
    }

    //PRINT OUTPUT 
    Serial.print("Distance: ");
    Serial.print(d);
    Serial.print(" cm | PWM Speed: ");
    Serial.print(pwm);
    Serial.print(" | Mode: ");
    Serial.println(mode);

    delay(300);
  }
}

long getDistanceCm() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH, 30000); 
  if (duration == 0) return 0;

  return (duration * 0.0343 / 2.0);  // convert to cm
}
