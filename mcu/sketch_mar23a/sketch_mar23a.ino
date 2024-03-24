#include <Arduino.h>
#include <HX711.h>

// Motor A
const int motorA1 = 2;
const int motorA2 = 3;
const int motorAPWM = 5;

// Motor B
const int motorB1 = 4;
const int motorB2 = 7;
const int motorBPWM = 6;

// HX711 pins
const int LOADCELL_DOUT_PIN = 9;
const int LOADCELL_SCK_PIN = 8;
HX711 scale;

void setup() {
  Serial.begin(9600);

  pinMode(motorA1, OUTPUT);
  pinMode(motorA2, OUTPUT);
  pinMode(motorAPWM, OUTPUT);
  pinMode(motorB1, OUTPUT);
  pinMode(motorB2, OUTPUT);
  pinMode(motorBPWM, OUTPUT);

  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');

    if (command.startsWith("MA") || command.startsWith("MB")) {
      handleMotorCommand(command);
    } else if (command.startsWith("HX")) {
      handleScaleCommand(command);
    }
  }
}

void handleMotorCommand(String command) {
  int pin1, pin2, pwmPin;
  if (command.startsWith("MA")) {
    pin1 = motorA1; pin2 = motorA2; pwmPin = motorAPWM;
  } else {
    pin1 = motorB1; pin2 = motorB2; pwmPin = motorBPWM;
  }

  char dir = command.charAt(2);
  int speed = command.substring(3).toInt();

  if (dir == 'F') {
    digitalWrite(pin1, HIGH);
    digitalWrite(pin2, LOW);
  } else {
    digitalWrite(pin1, LOW);
    digitalWrite(pin2, HIGH);
  }
  analogWrite(pwmPin, speed);
  
  Serial.println("Command executed: " + command);
}

void handleScaleCommand(String command) {
  if (command.substring(2) == "READ") {
    long reading = scale.read();
    Serial.println("HX711 Reading: " + String(reading));
  } else if (command.substring(2) == "TARE") {
    scale.tare();
    Serial.println("HX711 Tare done.");
  }
}
