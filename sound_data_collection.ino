
#define numInputs 3// number of analog inputs

uint8_t anaInput[numInputs] = {0, 1, 2};// pin numbers


volatile uint16_t anaValue[numInputs];// to store results (10-bit ADC fits in uint16_t)

// ADC Interrupt Service Routine - fires when a conversion is complete
ISR(ADC_vect) {
 static uint8_t i = 0;
 anaValue[i] = ADC;
 if (++i >= numInputs) i = 0; 
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
  const uint8_t FRAME_SIZE = 8;

  if (Serial.availableForWrite() >= FRAME_SIZE) {
      //Start Marker (1 byte)
      Serial.write('<');
      // Sends raw binary data
     Serial.write((byte*)&anaValue[0], sizeof(anaValue[0])); 
     Serial.write((byte*)&anaValue[1], sizeof(anaValue[1])); 
     Serial.write((byte*)&anaValue[2], sizeof(anaValue[2])); 
      // Send an End Marker (1 byte)
      Serial.write('>');
      
  }
  
}