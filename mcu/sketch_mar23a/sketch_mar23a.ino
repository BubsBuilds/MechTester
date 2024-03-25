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
    //Serial.println("Command received: " + command.substring(2));
    if (command.startsWith("MA") || command.startsWith("MB")) {
      handleMotorCommand(command);
    } else if (command.startsWith("HX")) {
      handleScaleCommand(command);
    }
  }
  //long reading = scale.read();
  //Serial.println(reading);
  //delay(200);
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

  if (dir == 'R') {
    digitalWrite(motorA1, HIGH);
    digitalWrite(motorA2, LOW);
    digitalWrite(motorB1, HIGH);
    digitalWrite(motorB2, LOW);

  } else {
    digitalWrite(motorA1, LOW);
    digitalWrite(motorA2, HIGH);
    digitalWrite(motorB1, LOW);
    digitalWrite(motorB2, HIGH);
  }
  analogWrite(motorAPWM, speed);
  analogWrite(motorBPWM, speed);
  
  Serial.println("Command executed: " + command);
}

void handleScaleCommand(String command) {
  if (command.substring(2) == "READ") {
    long reading = scale.read();
    delay(200);
    Serial.println("HX711 Reading: " + String(reading));
  } else if (command.substring(2) == "TARE") {
    scale.tare();
    Serial.println("HX711 Tare done.");
  }
}
