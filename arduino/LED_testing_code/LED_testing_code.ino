
const int ledGreen  = 2;   
const int ledYellow = 3;   
const int ledRed    = 4;   

void setup() {
  pinMode(ledGreen, OUTPUT);
  pinMode(ledYellow, OUTPUT);
  pinMode(ledRed, OUTPUT);

  digitalWrite(ledGreen, LOW);
  digitalWrite(ledYellow, LOW);
  digitalWrite(ledRed, LOW);
}

void loop() {


  digitalWrite(ledGreen, HIGH);
  delay(1000);
  digitalWrite(ledGreen, LOW);

  digitalWrite(ledYellow, HIGH);
  delay(1000);
  digitalWrite(ledYellow, LOW);

  digitalWrite(ledRed, HIGH);
  delay(1000);
  digitalWrite(ledRed, LOW);
}

