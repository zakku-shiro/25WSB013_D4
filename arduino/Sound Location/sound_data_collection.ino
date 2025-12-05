
#define numInputs 3// number of analog inputs

uint8_t anaInput[numInputs] = {0, 1, 2};// pin numbers


volatile uint16_t anaValue[numInputs];// to store results (10-bit ADC fits in uint16_t)

// ADC Interrupt Service Routine - fires when a conversion is complete
ISR(ADC_vect) {
  static uint8_t i = 0;

  anaValue[i] = ADC;
  if (++i >= numInputs) {i = 0;}
  //sets ref voltage
  ADMUX = 0x40 | anaInput[i];

  //conitinues with next input after reset
  ADCSRA |= (1 << ADSC);
}

void setup() {

 Serial.begin(500000); 

  // ADMUX: Set the reference voltage (AVCC) and select the first input A0 (0)
  ADMUX = 0x40 | anaInput[0];

  ADCSRA |= (1 << ADIE);//enable ADC Interrupt (ADIE)
  ADCSRA |= (1 << ADEN);// enable ADC (ADEN)
  ADCSRA |= (1 << ADSC);// start the first ADC conversion (ADSC)
}

void loop() {
  //const uint8_t FRAME_SIZE = 8;
  const uint8_t FRAME_SIZE = 6;
  uint8_t packed_data[4];

  if (Serial.availableForWrite() >= FRAME_SIZE) {
    //Start Marker
    Serial.write('<');
    // Sends raw binary data
    /*
    Serial.write((byte*)&anaValue[0], sizeof(anaValue[0])); 
    Serial.write((byte*)&anaValue[1], sizeof(anaValue[1])); 
    Serial.write((byte*)&anaValue[2], sizeof(anaValue[2])); 
    */
    //removes end 2 of mic 1
    packed_data[0] = (anaValue[0] >> 2) & 0xFF; 
    //last 2 values of m1 shifted left 6, removes end half of m2 
    packed_data[1] = ((anaValue[0] & 0x03) << 6) | ((anaValue[1] >> 4) & 0x3F); 
    //moves end half of m2 4 bits left, only keeps first 2 bits of m3 as last 2 bits
    packed_data[2] = ((anaValue[1] & 0x0F) << 4) | ((anaValue[2] >> 6) & 0x0F); 
    //rest of m3
    packed_data[3] = (anaValue[2] & 0x3F); 

    Serial.write(packed_data, 4);

    //End Marker
    Serial.write('>');
      
  }
  
}
