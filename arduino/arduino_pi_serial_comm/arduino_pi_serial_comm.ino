#define SYNC1 0xBE
#define SYNC2 0xEF
#define PACKET_BUFFER_SIZE 32
#define MOVE_PACKET_LENGTH 1
#define LED_PACKET_LENGTH 1

// Signals
enum {
  SIG_ZERO = 0,
  SIG_ERROR,
  SIG_ACKNOWLEDGE,
  SIG_SOUND_DATA,
  SIG_LED_COMMAND,
  SIG_MOVE_COMMAND
};
const unsigned long BAUD_RATE = 500000;

// LED Control Variables
bool  g_isLEDOn = false,
      g_isBlinking = false;
unsigned long g_TargetTime = 0;

// Packet Format: | SYNC1 | SYNC2 | TYPE | LEN | PAYLOAD | CRC |
void parseSerial() {
  static uint8_t decodeState = 0;
  static uint8_t msg_type;
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

    switch(decodeState) {
      case WAIT_SYNC1:
        if (incomingByte == SYNC1) decodeState = WAIT_SYNC2;
        break;

      case WAIT_SYNC2:
        if (incomingByte == SYNC2) decodeState = WAIT_TYPE;
        else decodeState = WAIT_SYNC1;
        break;

      case WAIT_TYPE:
        msg_type = incomingByte;
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
        decodeState = WAIT_PAYLOAD;
        break;

      case WAIT_PAYLOAD:
        buffer[index++] = incomingByte;
        crc ^= incomingByte;

        if (index >= length)
          decodeState = 5;
        break;

      case WAIT_CRC:
        if (crc == incomingByte)
          handlePacket(msg_type, buffer, length);

        decodeState = 0;
        break;
    }
  }
}

void handlePacket(uint8_t msg_type, uint8_t *data, uint8_t length) {
  bool invalidPacketLength = false;

  switch (msg_type) {
    case SIG_LED_COMMAND: {
      if (length != LED_PACKET_LENGTH) {
        invalidPacketLength = true;
        break;
      }

      g_isBlinking = *data;
      if (!g_isBlinking) { // Ensure LED turns off
        digitalWrite(LED_BUILTIN, LOW);
        g_isLEDOn = false;
      }

      break;
    }

    case SIG_MOVE_COMMAND: {
      if (length != MOVE_PACKET_LENGTH) {
        invalidPacketLength = true;
        break;
      }
      
      enum {
        STOP = 0,
        REVERSE,
        FORWARD,
        LEFT_TURN,
        RIGHT_TURN
      };

      switch (*data) {
        case STOP:
          break;
        case REVERSE:
          break;
        case FORWARD:
          break;
        case LEFT_TURN:
          break;
        case RIGHT_TURN:
          break;
      }
      break;
    }
  }

  if (invalidPacketLength) {
    uint8_t err = 1;
    sendPacket(SIG_ERROR, &err, 1);
  } else {
    sendPacket(SIG_ACKNOWLEDGE, 0, 0);
  }
}

void sendPacket(uint8_t msg_type, uint8_t *payload, uint8_t length) {
  if (Serial.availableForWrite() < (length + 5))
    return;

  uint8_t crc = msg_type ^ length;

  Serial.write(SYNC1);
  Serial.write(SYNC2);
  Serial.write(msg_type);
  Serial.write(length);

  for (uint8_t i = 0; i < length; i++)
  {
    Serial.write(payload[i]);
    crc ^= payload[i];
  }

  Serial.write(crc);
}

#define NUM_INPUTS 3// number of analog inputs
volatile uint16_t anaValue[NUM_INPUTS];// to store results (10-bit ADC fits in uint16_t)
volatile bool isFrameReady = false;

// ADC Interrupt Service Routine - fires when a conversion is complete
ISR(ADC_vect) {
  static uint8_t i = 0;

  anaValue[i] = ADC;
  i++;

  if (i >= NUM_INPUTS) {
    i = 0;
    isFrameReady = true;
  }

  ADMUX = 0x40 | i;
  ADCSRA |= (1 << ADSC);
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);

  Serial.begin(BAUD_RATE);

  // Wait for serial port to connect. Needed for native USB
  uint8_t counter = 0;
  while (!Serial) {
    digitalWrite(LED_BUILTIN, counter++ % 2);
  }

  // ADMUX: Set the reference voltage (AVCC) and select the first input A0 (0)
  ADMUX = 0x40; //| 0;

  ADCSRA |= (1 << ADIE);//enable ADC Interrupt (ADIE)
  ADCSRA |= (1 << ADEN);// enable ADC (ADEN)
  ADCSRA |= (1 << ADSC);// start the first ADC conversion (ADSC)
}


void loop() {
  // Communications Check
  parseSerial();

  uint8_t packed_data[4];
  if (isFrameReady) {
    isFrameReady = false;
    //removes end 2 of mic 1
    packed_data[0] = (anaValue[0] >> 2) & 0xFF;
    //last 2 values of m1 shifted left 6, removes end half of m2
    packed_data[1] = ((anaValue[0] & 0x03) << 6) | ((anaValue[1] >> 4) & 0x3F);
    //moves end half of m2 4 bits left, only keeps first 2 bits of m3 as last 2 bits
    packed_data[2] = ((anaValue[1] & 0x0F) << 4) | ((anaValue[2] >> 6) & 0x0F);
    //rest of m3
    packed_data[3] = (anaValue[2] & 0x3F);

    sendPacket(SIG_SOUND_DATA, (uint8_t*)&packed_data, 4);
  }
  
  // LED Handler
  if (g_isBlinking) {
    if (millis() >= g_TargetTime) {
      if (g_isLEDOn) {
        digitalWrite(LED_BUILTIN, LOW);
        g_isLEDOn = false;
        g_TargetTime = millis() + 100; // turn on in 1 tenth of a second (100 milliseconds)
      } else {
        digitalWrite(LED_BUILTIN, HIGH);
        g_isLEDOn = true;
        g_TargetTime = millis() + 100; // turn off in 1 tenth of a second (100 milliseconds)
      }
    }
  }
}

