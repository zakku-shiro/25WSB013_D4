// Movement Definitions
#define PIN_MOTOR_1_SPEED 0x06
#define PIN_MOTOR_1_DIRECTION 0x08
#define PIN_MOTOR_2_SPEED 0x05
#define PIN_MOTOR_2_DIRECTION 0x07
// US Sensor Defs
#define US_TRIG_PIN 0x09
#define US_ECHO_PIN 0x0A
#define US_SEND_RATE_MS 250

#define MOTOR_FORWARD LOW
#define MOTOR_REVERSE HIGH

#define MOTOR_MAX_SPEED 255

// Comms Definitions
#define BAUD_RATE 500000
#define SYNC1 0xBE
#define SYNC2 0xEF
#define PACKET_BUFFER_SIZE 32

#define MOVE_PACKET_LENGTH 4
#define LED_PACKET_LENGTH 2

// Control Pins
#define DEMO_ENABLED_LED 0x00
#define MODE_SELECT_LED  0x01
#define STATUS_LED 0x02
#define DEMO_ENABLED_SWITCH 0x03
#define MODE_SELECT_SWITCH 0x04

enum {
  SIG_PING = 0,
  SIG_ERROR,
  SIG_ACKNOWLEDGE,
  SIG_SOUND_DATA,
  SIG_LED_COMMAND,
  SIG_MOVE_COMMAND,
  SIG_ULTRASONIC_DATA,
};
static bool g_HasBeenAcknowledged;

// Watchdog Configs
unsigned long g_lastCommandTime = 0;
#define COMMAND_TIMEOUT_MS 500

// US Controls
unsigned long g_lastUltrasonicPacketTime = 0;

// LED Controls
enum {
  OFF = 0,
  ON,
  SLOW_BLINK,
  FAST_BLINK
};  // LED Modes
#define BLINKING_TIME 200

bool g_isOnboardLEDOn = false,
     g_isOnboardLEDBlinking = false,
     g_isStatusLEDOn = false;
unsigned long g_OnboardLEDTargetTime = 0,
              g_StatusLEDTargetTime = 0;
uint8_t g_CurrentStatusLEDMode = OFF;

void setLeftMotorSpeed(uint8_t speed) {
  analogWrite(PIN_MOTOR_1_SPEED, speed);
}

void setLeftMotorDirection(uint8_t direction) {
  digitalWrite(PIN_MOTOR_1_DIRECTION, direction);
}

void setRightMotorSpeed(uint8_t speed) {
  analogWrite(PIN_MOTOR_2_SPEED, speed);
}

void setRightMotorDirection(uint8_t direction) {
  digitalWrite(PIN_MOTOR_2_DIRECTION, direction);
}

float getDistanceCm() {
  digitalWrite(US_TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(US_TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(US_TRIG_PIN, LOW);

  long duration = pulseIn(US_ECHO_PIN, HIGH, 15000);

  if (duration == 0) {
    return 0;
  }
  
  // Formula for distance
  float distance = duration * 0.0343 / 2.0;
  return distance;
}

/*
  Packet Format:
  | SYNC1 | SYNC2 | TYPE | LEN | PAYLOAD | CRC |
*/
void parseSerial() {
  static uint8_t decodeState = 0;
  static uint8_t msgType;
  static uint8_t length;
  static uint8_t buffer[PACKET_BUFFER_SIZE];
  static uint8_t index;
  static uint8_t crc;

  enum {
    WAIT_SYNC1,
    WAIT_SYNC2,
    WAIT_TYPE,
    WAIT_LEN,
    WAIT_PAYLOAD,
    WAIT_CRC
  };

  while (Serial.available()) {
    uint8_t incomingByte = Serial.read();

    switch (decodeState) {
      case WAIT_SYNC1:
        if (incomingByte == SYNC1) decodeState = WAIT_SYNC2;
        break;

      case WAIT_SYNC2:
        if (incomingByte == SYNC2) decodeState = WAIT_TYPE;
        else decodeState = WAIT_SYNC1;
        break;

      case WAIT_TYPE:
        msgType = incomingByte;
        crc = incomingByte;
        decodeState = WAIT_LEN;
        break;

      case WAIT_LEN:
          length = incomingByte;
          if (length > PACKET_BUFFER_SIZE) { 
            decodeState = WAIT_SYNC1; 
            break;
          }
          crc ^= incomingByte;
          index = 0;
          decodeState = (length == 0) ? WAIT_CRC : WAIT_PAYLOAD;
          break;

      case WAIT_PAYLOAD:
        buffer[index++] = incomingByte;
        crc ^= incomingByte;

        if (index >= length)
          decodeState = WAIT_CRC;
        break;

      case WAIT_CRC:
        if (crc == incomingByte)
          handlePacket(msgType, buffer, length);

        decodeState = WAIT_SYNC1;
        break;
    }
  }
}

void handlePacket(uint8_t msg_type, uint8_t *data, uint8_t length) {
  bool invalidPacketLength = false;

  switch (msg_type) {
    case SIG_PING:
      sendPacket(SIG_ACKNOWLEDGE, 0, 0);
      return;

    case SIG_ACKNOWLEDGE:
      g_HasBeenAcknowledged = true;
      return;

    case SIG_LED_COMMAND: {
      if (length != LED_PACKET_LENGTH) {
        invalidPacketLength = true;
        break;
      }

      uint8_t pinIndex = data[0];
      uint8_t newStatus = data[1];

      switch (pinIndex) {
        case DEMO_ENABLED_LED:
          break;
        case MODE_SELECT_LED:
          break;
        case STATUS_LED:
          g_CurrentStatusLEDMode = newStatus;
          break;
        default:
          break;
      }

      break;
    }

    case SIG_MOVE_COMMAND: {
      if (length != MOVE_PACKET_LENGTH) {
        invalidPacketLength = true;
        break;
      }

      setLeftMotorDirection(data[0] ? MOTOR_REVERSE : MOTOR_FORWARD);
      setRightMotorDirection(data[2] ? MOTOR_REVERSE : MOTOR_FORWARD);
      setLeftMotorSpeed((uint8_t)data[1]);
      setRightMotorSpeed((uint8_t)data[3]);

      // Update watchdog timer
      g_lastCommandTime = millis();

      break;
    }

    default: {
      uint8_t err = 2;
      sendPacket(SIG_ERROR, &err, 1);
      return;
    }
  }

  if (invalidPacketLength) {
    uint8_t err = 1;
    sendPacket(SIG_ERROR, &err, 1);
  } else {
    sendPacket(SIG_ACKNOWLEDGE, 0, 0);
  }
}

/*
    Packet Sender
*/
void sendPacket(uint8_t msgType, uint8_t *payload, uint8_t length) {
  if (Serial.availableForWrite() < (length + 5))
    return;

  uint8_t crc = msgType ^ length;

  Serial.write(SYNC1);
  Serial.write(SYNC2);
  Serial.write(msgType);
  Serial.write(length);

  for (uint8_t i = 0; i < length; i++) {
    Serial.write(payload[i]);
    crc ^= payload[i];
  }

  Serial.write(crc);
}

#define MIC_COUNT 3 // number of analog inputs
volatile uint16_t anaValue[MIC_COUNT];  // to store results (10-bit ADC fits in uint16_t)
volatile bool isFrameReady = false;

// ADC Interrupt Service Routine - fires when a conversion is complete
ISR(ADC_vect) {
  static uint8_t i = 0;

  anaValue[i] = ADC;
  i++;

  if (i >= MIC_COUNT) {
    i = 0;
    isFrameReady = true;
  }

  ADMUX = 0x40 | i;
  ADCSRA |= (1 << ADSC);
}

void setup() {
  pinMode(PIN_MOTOR_1_SPEED, OUTPUT);
  pinMode(PIN_MOTOR_1_DIRECTION, OUTPUT);
  pinMode(PIN_MOTOR_2_SPEED, OUTPUT);
  pinMode(PIN_MOTOR_2_DIRECTION, OUTPUT);
  pinMode(US_TRIG_PIN, OUTPUT);
  pinMode(US_ECHO_PIN, INPUT);
  pinMode(LED_BUILTIN, OUTPUT);

  // Zero Movement
  setLeftMotorSpeed(0);
  setRightMotorSpeed(0);
  
  /* Sound Setup*/
  // ADMUX: Set the reference voltage (AVCC) and select the first input A0 (0)
  ADMUX = 0x40; //| 0;

  ADCSRA |= (1 << ADIE);  //enable ADC Interrupt (ADIE)
  ADCSRA |= (1 << ADEN);  // enable ADC (ADEN)
  ADCSRA |= (1 << ADSC);  // start the first ADC conversion (ADSC)

  Serial.begin(BAUD_RATE);
  uint8_t counter = 0;
  while (!Serial) {
    digitalWrite(LED_BUILTIN, counter++ % 2);
  }

  
}

void loop() {
  parseSerial();

  // Watchdog safety stop
  if (millis() - g_lastCommandTime > COMMAND_TIMEOUT_MS) {
    setLeftMotorSpeed(0);
    setRightMotorSpeed(0);
    setLeftMotorDirection(MOTOR_FORWARD);
    setRightMotorDirection(MOTOR_FORWARD);
  }

  // Ultrasonic Data Sending
  if (millis() - g_lastUltrasonicPacketTime > US_SEND_RATE_MS) {
    float distance = getDistanceCm();
    sendPacket(SIG_ULTRASONIC_DATA, (uint8_t*)&distance, sizeof(float));
    g_lastUltrasonicPacketTime = millis();
  }

  // Microphone Data Sending
  uint8_t packed_mic_data[4];
  if (isFrameReady) {
    isFrameReady = false;
    //removes end 2 of mic 1
    packed_mic_data[0] = (anaValue[0] >> 2) & 0xFF;
    //last 2 values of m1 shifted left 6, removes end half of m2
    packed_mic_data[1] = ((anaValue[0] & 0x03) << 6) | ((anaValue[1] >> 4) & 0x3F);
    //moves end half of m2 4 bits left, only keeps first 2 bits of m3 as last 2 bits
    packed_mic_data[2] = ((anaValue[1] & 0x0F) << 4) | ((anaValue[2] >> 6) & 0x0F);
    //rest of m3
    packed_mic_data[3] = (anaValue[2] & 0x3F);

    sendPacket(SIG_SOUND_DATA, (uint8_t*)&packed_mic_data, 4);
  }

  // LED Blink Handler - Horrific
  if (g_isOnboardLEDBlinking) {
    if (millis() >= g_OnboardLEDTargetTime) {
      if (g_isOnboardLEDOn) {
        digitalWrite(LED_BUILTIN, LOW);
        g_isOnboardLEDOn = false;
      } else {
        digitalWrite(LED_BUILTIN, HIGH);
        g_isOnboardLEDOn = true;
      }
      g_OnboardLEDTargetTime = millis() + BLINKING_TIME;
    }
  }

  switch (g_CurrentStatusLEDMode) {
    default:
    case OFF:
      if (g_isStatusLEDOn != false) {
        digitalWrite(STATUS_LED, LOW);
        g_isStatusLEDOn = false;
      }
      break;
    case ON:
      if (g_isStatusLEDOn != true) {
        digitalWrite(STATUS_LED, HIGH);
        g_isStatusLEDOn = true;
      }
      break;
    case SLOW_BLINK:
      if (millis() >= g_StatusLEDTargetTime) {
        g_isStatusLEDOn = !g_isStatusLEDOn;
        digitalWrite(STATUS_LED, g_isStatusLEDOn);
        g_StatusLEDTargetTime = millis() + BLINKING_TIME;
      }
      break;
    case FAST_BLINK:
      if (millis() >= g_StatusLEDTargetTime) {
        g_isStatusLEDOn = !g_isStatusLEDOn;
        digitalWrite(STATUS_LED, g_isStatusLEDOn);
        g_StatusLEDTargetTime = millis() + BLINKING_TIME / 2;
      }
      break;
  }
}