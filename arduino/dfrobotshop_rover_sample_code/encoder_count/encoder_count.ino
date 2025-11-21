/* The code below simply counts the number of changes,
 so a disc with 8x white sections and 8x cutouts will
 provide a count of 16 per 360 degree rotation. It is
 up to you to integrate it with your code*/

int rawsensorValue = 0; // variable to store the value coming from the sensor
int sensorcount0 = 0;
int sensorcount1 = 0;
long count = 0;

void setup() {
  int i;
  for(i=5;i<=8;i++)
    pinMode(i, OUTPUT);
  Serial.begin(9600);
  int leftspeed = 255; //255 is maximum speed
  int rightspeed = 255;
}

void loop() {
  analogWrite (10,255);
  digitalWrite(12,LOW);
  analogWrite (11,255);
  digitalWrite(13,LOW);
  delay(20);
  rawsensorValue = analogRead(0);
  if (rawsensorValue < 600){ //Min value is 400 and max value is 800, so state chance can be done at 600.
    sensorcount1 = 1;
  }
  else {
    sensorcount1 = 0;
  }
  if (sensorcount1 != sensorcount0){
    count ++;
  }
  sensorcount0 = sensorcount1;
  Serial.println(count);
}
