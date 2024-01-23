#include <util/delay.h>
const int switchPin = 8;
const int pin7 = 7;
const int pin6 = 6;
int is_high = 1;
void setup() {
  pinMode(switchPin, INPUT_PULLUP);
  pinMode(pin7, OUTPUT);
  pinMode(pin6, OUTPUT);
  Serial.begin(115200);
  Serial.println("Bootin");
}

void loop() {
  if (is_high == 1 && digitalRead(switchPin) == LOW) {
    is_high = 0;
    // digitalWrite(pin7, HIGH);
    PORTD = B10000000;
    _delay_us(0.4);
    // digitalWrite(pin6, HIGH);
    PORTD = B01000000;
    _delay_us(2);
    // digitalWrite(pin7, LOW);
    PORTD = B01000000;
    _delay_us(1);
    // digitalWrite(pin6, LOW);
    PORTD = B00000000;
    Serial.println("Switch activated");
  }
  if (is_high == 0 && digitalRead(switchPin) == HIGH){
    is_high = 1;
    Serial.println("Switch Reset");
  }
}
