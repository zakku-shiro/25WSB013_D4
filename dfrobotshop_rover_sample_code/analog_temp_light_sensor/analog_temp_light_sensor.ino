/* To read the onboard light and temperature sensors,
 run the code below, then open the serial window at
 9600 baud. Ensure the two jumpers are in place*/

int LightValue = 0;
int TemperatureValue = 0;

void setup() {
  Serial.begin(9600);
}

void loop() {
  LightValue = analogRead(A0);
  TemperatureValue = analogRead(A1);
  Serial.print("Light: ");
  Serial.print(LightValue);
  Serial.print(" Temperature: ");
  Serial.println(TemperatureValue);
  delay(100);
}

