
int E1 = 6; 
int E2 = 5;
int M1 = 8; 
int M2 = 7; 


const int trigPin = 9;   
const int echoPin = 10;  

const int ledGreen  = 2;  
const int ledYellow = 3;  
const int ledRed    = 4;  

bool validatedAt30 = false;
bool validatedAt20 = false;



void setup(void)
{
  for (int i = 5; i <= 8; i++) {
    pinMode(i, OUTPUT);
  }

  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  digitalWrite(trigPin, LOW); 

  pinMode(ledGreen, OUTPUT);
  pinMode(ledYellow, OUTPUT);
  pinMode(ledRed, OUTPUT);

  // Serial for debug / demonstration
  Serial.begin(9600);
  Serial.println("=== Robot search + hone demo starting ===");
}

void loop(void)
{
  runDemoOnce();

  while (true) { }
}


void runDemoOnce() {
  // 1) full 360° spin with green LED
  setModeSearching();
  doFull360Search();

  // turn 180° to face the source
  processAndTurnTowardsSource();

  // move towards the source using ultrasonics yellow LED
  setModeHoning();
  approachToSource();

  // robot stops we set red LED there
}


void setModeSearching() {
  digitalWrite(ledGreen, HIGH);
  digitalWrite(ledYellow, LOW);
  digitalWrite(ledRed, LOW);
}

void setModeHoning() {
  digitalWrite(ledGreen, LOW);
  digitalWrite(ledYellow, HIGH);
  digitalWrite(ledRed, LOW);
}

void setModeComplete() {
  digitalWrite(ledGreen, LOW);
  digitalWrite(ledYellow, LOW);
  digitalWrite(ledRed, HIGH);
}

// 360° SEARCH 

void doFull360Search() {
  Serial.println();
  Serial.println("[SEARCH] Starting 360-degree scan (green LED ON)");

  for (int c = 0; c < 68; c++) {
    turn_left();  
  }

  stop(); // stop motors after the spin
  Serial.println("[SEARCH] 360-degree scan complete.");
}

// TURN 180° 

void processAndTurnTowardsSource() {
  Serial.println();
  Serial.println("[PROCESS] Analysing detected sound/light...");
  delay(2000);  // simulate processing

  Serial.println("[PROCESS] Turning to face source (180 degrees turn).");

  for (int c = 0; c < 34; c++) {
    turn_left();
  }

  stop();
  Serial.println("[PROCESS] Now facing towards the source.");
}

// APPROACH ULTRASONIC

void approachToSource() {
  Serial.println();
  Serial.println("[HONE] Beginning approach towards source (yellow LED ON)");

  validatedAt30 = false;
  validatedAt20 = false;

  while (true) {
    long d = getDistanceCm();  //  distance  cm

    if (d == 0) {
      
      Serial.println("No valid ultrasonic reading (distance = 0).");
      stop();
      delay(300);
      continue;
    }

    // CHECKPOINT @ ~30 cm 
    if (!validatedAt30 && d <= 30 && d > 20) {
      stop();  // stop motors
      Serial.println();
      Serial.println("[HONE] CHECKPOINT: ~30 cm reached");
      Serial.println("[HONE] Validating direction (simulated)...");
      delay(5000);  // 5 seconds pause to simulate double-check
      Serial.println("[HONE] Direction confirmed. Continuing approach.");
      Serial.println();
      validatedAt30 = true;
    }

    //CHECKPOINT @ ~20 cm 
    if (!validatedAt20 && d <= 20 && d > 10) {
      stop();  // stop motors
      Serial.println();
      Serial.println("[HONE] CHECKPOINT: ~20 cm reached");
      Serial.println("[HONE] Validating direction (simulated)...");
      delay(5000);  // pause to simulate 
      Serial.println("[HONE] Direction confirmed. Continuing approach.");
      Serial.println();
      validatedAt20 = true;
    }

    // PWM SPEED MAPPING 
    int pwm = 0;
    const char* mode = "";

    if (d > 50) {
      pwm = 255;  // far away: full speed
      mode = "APPROACH FAST (>50cm)";
    }
    else if (d > 30) {
      pwm = 255;  // 50–30 cm: full speed
      mode = "APPROACH FAST (50–30cm)";
    }
    else if (d > 20) {
      pwm = 255;  // 30–20 cm: full speed
      mode = "APPROACH FAST (30–20cm)";
    }
    else if (d > 10) {
      pwm = 128;  // 20–10 cm: half speed
      mode = "APPROACH MEDIUM (20–10cm)";
    }
    else if (d > 5) {
      pwm = 64;   // 10–5 cm: slow creep
      mode = "APPROACH SLOW (10–5cm)";
    }
    else {
      pwm = 0;    // <=5 cm: stop
      mode = "TARGET REACHED";
    }

   //TARGET REACHED
    if (pwm == 0) {
      stop();            // stop all motors
      setModeComplete(); // red LED ON
      Serial.println();
      Serial.print("Distance: ");
      Serial.print(d);
      Serial.println(" cm");
      Serial.println("PWM Speed: 0");
      Serial.println("Mode: TARGET REACHED");
      Serial.println("Distance has been met, all motors off, source detected.");
      Serial.println("==============================================");
      break; // exit approach loop
    }

    forwardSpeed(pwm);


    Serial.print("Distance: ");
    Serial.print(d);
    Serial.print(" cm | PWM Speed: ");
    Serial.print(pwm);
    Serial.print(" | Mode: ");
    Serial.println(mode);

    delay(300);  // small dela
  }
}



long getDistanceCm() {
 
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);


  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  // Measure how long echoPin stays HIGH 
  long duration = pulseIn(echoPin, HIGH, 30000); 

  if (duration == 0) {
  
    return 0;
  }

  // Convert time to distance:
  // distance (cm) = (duration * 0.0343) / 2
  long distance = duration * 0.0343 / 2.0;
  return distance;
}


void stop(void)          // Stop both motors
{
  digitalWrite(E1, LOW);
  digitalWrite(E2, LOW);
  Serial.println("stop");
}

void forwardSpeed(int pwm) 
{
  pwm = constrain(pwm, 0, 255);

  analogWrite(E1, pwm);  // Motor 1 speed
  digitalWrite(M1, LOW); // Motor 1 direction 
  analogWrite(E2, pwm);  // Motor 2 speed
  digitalWrite(M2, LOW); // Motor 2 direction 
  Serial.print("forward at PWM=");
  Serial.println(pwm);
}

void forward (void)      // Forward at full speed, 
{
  forwardSpeed(255);
  delay(100);
}

void reverse (void)       // Reverse at full speed, 100ms
{
  analogWrite(E1, 255);
  digitalWrite(M1, HIGH);
  analogWrite(E2, 255);
  digitalWrite(M2, HIGH);
  Serial.println("reverse");
  delay(100);
}

void turn_left (void)    
{
  analogWrite(E1, 127);   // Motor 1 half speed
  digitalWrite(M1, HIGH); // Motor 1 backwards
  analogWrite(E2, 127);   // Motor 2 half speed
  digitalWrite(M2, LOW);  // Motor 2 forwards
  Serial.println("left");
  delay(100);
}

void turn_right (void)    // Turn right
{
  analogWrite(E1, 127);   // Motor 1 half speed
  digitalWrite(M1, LOW);  // Motor 1 forwards
  analogWrite(E2, 127);   // Motor 2 half speed
  digitalWrite(M2, HIGH); // Motor 2 backwards
  Serial.println("right");
  delay(100);
}
