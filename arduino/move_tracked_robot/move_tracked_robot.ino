/*To control the rover, Copy and paste the code below into the Arduino software*/
int E1 = 6; //M1 Speed Control
int E2 = 5; //M2 Speed Control
int M1 = 8; //M1 Direction Control
int M2 = 7; //M2 Direction Control

void setup(void)
{
  int i;
  for(i=5;i<=8;i++)
  pinMode(i, OUTPUT);
  Serial.begin(9600);
  Serial.println("setup");
}
 
void loop(void)           //main program
{
  int c;
 
  {
  
      for(c=1;c<=20;c++)   //move forward by approx. 20cm by executing the forward subroutine 20 times
        {
        forward();  
        }
      
      for(c=1;c<=17;c++)   //turn left by approx. 90 degrees by executing the turn_left subroutine 15 times
        {
        turn_left(); 
        }
        
      for(c=1;c<=5;c++)    //move forward by approx. 5cm by executing the forward subroutine 5 times
        {
        forward(); 
        }

      for(c=1;c<=17;c++)   //turn right by approx. 90 degrees by executing the turn_left subroutine 15 times
        {
        turn_right();  
        }
        
      for(c=1;c<=20;c++)     //move backwards by approx. 20cm by executing the forward subroutine 20 times
        {
        reverse();  
        }
        
      stop();
  
  }
}

void stop(void)          //Stop subroutine
{
  digitalWrite(E1,LOW);
  digitalWrite(E2,LOW);
  Serial.println("stop");
}

void forward (void)      //forward subroutine
{
  analogWrite (E1,255);  //Motor 1 full speed (value of 255 = full speed)
  digitalWrite(M1,LOW);  //Motor 1 direction control
  analogWrite (E2,255);  //Motor 2 full speed (value of 255 = full speed)
  digitalWrite(M2,LOW);  //Motor 2 direction control
  Serial.println("forward");
  delay(100);
}

void reverse (void)       //reverse subroutine
{
  analogWrite (E1,255);   //Motor 1 half speed (value of 255 = full speed)
  digitalWrite(M1,HIGH);  //Motor 1 direction control
  analogWrite (E2,255);   //Motor 2 half speed (value of 255 = full speed)
  digitalWrite(M2,HIGH);  //Motor 2 direction control
  Serial.println("reverse");
  delay(100);
}

void turn_left (void)     //turn_left subroutine
{
  analogWrite (E1,127);   //Motor 1 half speed (value of 127 = half speed)
  digitalWrite(M1,HIGH);  //Motor 1 direction control
  analogWrite (E2,127);   //Motor 2 half speed (value of 127 = half speed)
  digitalWrite(M2,LOW);   //Motor 2 direction control
  Serial.println("left");
  delay(100);
}

void turn_right (void)    //turn_right subroutine
{
  analogWrite (E1,127);   //Motor 1 half speed (value of 127 = half speed)
  digitalWrite(M1,LOW);   //Motor 1 direction control
  analogWrite (E2,127);   //Motor 2 half speed (value of 127 = half speed)
  digitalWrite(M2,HIGH);  //Motor 2 direction control
  Serial.println("right");
  delay(100);
}

 
