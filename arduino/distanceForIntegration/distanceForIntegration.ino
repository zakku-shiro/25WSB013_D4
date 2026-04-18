const int trigPin = 9;   
const int echoPin = 10;  

void setup(void)
{
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  digitalWrite(trigPin, LOW); 
  Serial.begin(9600);
}



void loop(void)
{
  //printing into serial monitor 
  long d = getDistanceCm();

  Serial.print("Distance: ");
  Serial.print(d);
  Serial.println(" cm");

  delay(300);
}
// duration measuring protocol 
long getDistanceCm() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH, 30000); 

  if (duration == 0) {
    return 0;
  }
// maths to work out distance 
  long distance = duration * 0.0343 / 2.0;
  return distance;
}