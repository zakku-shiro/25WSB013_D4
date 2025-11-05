/* To control the Rover, copy and paste the code below into the Arduino
 software. Ensure the motors are connected to the correct pins. The
 code does not factor in encoders at this time*/

//Front motors
int E1 = 10 ; //M1 Speed Control
int E2 = 11; //M2 Speed Control
int M1 = 12; //M1 Direction Control
int M2 = 13; //M2 Direction Control

//Rear motors
int E3 = 6; //M1 Speed Control
int E4 = 5; //M2 Speed Control
int M3 = 8; //M1 Direction Control
int M4 = 7; //M2 Direction Control

void setup(void)
{
  int i;
  for(i=3;i<=13;i++)
  pinMode(i, OUTPUT);
  Serial.begin(115200);
}

void loop(void)
{
  while (Serial.available() < 1) {} // Wait until a character is received
  char val = Serial.read();
  int leftspeed = 255; //255 is maximum speed
  int rightspeed = 255;
  switch(val) // Perform an action depending on the command
  {
    case 'w'://Move Forward
    case 'W':
      forward (leftspeed,rightspeed);
      break;
    case 's'://Move Backwards
    case 'S':
      reverse (leftspeed,rightspeed);
      break;
    case 'a'://Turn Left
    case 'A':
      left (leftspeed,rightspeed);
      break;
    case 'd'://Turn Right
    case 'D':
      right (leftspeed,rightspeed);
      break;
    case 'q'://rotate ccw
    case 'Q':
      ccw (leftspeed,rightspeed);
      break;
    case 'e'://rotate cw
    case 'E':
      cw (leftspeed,rightspeed);
      break;
    case 'z'://move at 45 degrees
    case 'Z':
      fortyfive (leftspeed,rightspeed);
      break;
    case 'x'://move at 135 degrees
    case 'X':
      onethirtyfive (leftspeed,rightspeed);
      break;
    // to move at 225 and 315, use the 45 degree and 135 degree
    // code but reverse motor direction.
    default:
      stop();
      break;
  }
}

void stop(void) //Stop
{
  digitalWrite(E1,LOW);
  digitalWrite(E2,LOW);
  digitalWrite(E3,LOW);
  digitalWrite(E4,LOW);
}

void forward(char a,char b)
{
  analogWrite (E1,a);
  digitalWrite(M1,LOW);
  analogWrite (E2,b);
  digitalWrite(M2,HIGH);
  analogWrite (E3,a);
  digitalWrite(M3,LOW);
  analogWrite (E4,b);
  digitalWrite(M4,HIGH);
}

void reverse (char a,char b)
{
  analogWrite (E1,a);
  digitalWrite(M1,HIGH);
  analogWrite (E2,b);
  digitalWrite(M2,LOW);
  analogWrite (E3,a);
  digitalWrite(M3,HIGH);
  analogWrite (E4,b);
  digitalWrite(M4,LOW);
}

void ccw (char a,char b)
{
  analogWrite (E1,a);
  digitalWrite(M1,HIGH);
  analogWrite (E2,b);
  digitalWrite(M2,HIGH);
  analogWrite (E3,a);
  digitalWrite(M3,HIGH);
  analogWrite (E4,b);
  digitalWrite(M4,LOW);
}

void cw (char a,char b)
{
  analogWrite (E1,a);
  digitalWrite(M1,LOW);
  analogWrite (E2,b);
  digitalWrite(M2,LOW);
  analogWrite (E3,a);
  digitalWrite(M3,LOW);
  analogWrite (E4,b);
  digitalWrite(M4,HIGH);
}

void left (char a,char b)
{
  analogWrite (E1,a);
  digitalWrite(M1,HIGH);
  analogWrite (E2,b);
  digitalWrite(M2,HIGH);
  analogWrite (E3,a);
  digitalWrite(M3,LOW);
  analogWrite (E4,b);
  digitalWrite(M4,LOW);
}

void right (char a,char b)
{
  analogWrite (E1,a);
  digitalWrite(M1,LOW);
  analogWrite (E2,b);
  digitalWrite(M2,LOW);
  analogWrite (E3,a);
  digitalWrite(M3,HIGH);
  analogWrite (E4,b);
  digitalWrite(M4,HIGH);
}

void fortyfive (char a,char b)
{
  analogWrite (E1,a);
  digitalWrite(M1,LOW);
  analogWrite (E3,a);
  digitalWrite(M3,LOW);
}

void onethirtyfive (char a,char b)
{
  analogWrite (E2,b);
  digitalWrite(M2,HIGH);
  analogWrite (E4,b);
  digitalWrite(M4,HIGH);
}
