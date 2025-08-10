#include <Arduino.h>
#include <HX711.h>

// Motor A
const int motorA1 = 7;
const int motorA2 = 8;
const int motorAPWM = 11;

// // Motor B
// const int motorB1 = 4;
// const int motorB2 = 7;
// const int motorBPWM = 6;

// HX711 pins
const int LOADCELL_DOUT_PIN = 4;
const int LOADCELL_SCK_PIN = 5;
long lcVal;
HX711 scale;
long lcTareOff = 0;
int lcTareCount = 5;

// int dispSenseVal;
// int dispSensePin = A0;

void setup() {
  Serial.begin(115200);

  pinMode(motorA1, OUTPUT);
  pinMode(motorA2, OUTPUT);
  pinMode(motorAPWM, OUTPUT);
  // pinMode(motorB1, OUTPUT);
  // pinMode(motorB2, OUTPUT);
  // pinMode(motorBPWM, OUTPUT);

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
    } else if (command.startsWith("CL")){
      handleLCCommand(command);
    } else if (command.startsWith("LF")){
      handleL2F(command);
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
    // pin1 = motorB1; pin2 = motorB2; pwmPin = motorBPWM;
  }

  char dir = command.charAt(2);
  int speed = command.substring(3).toInt();

  if (dir == 'R') {
    digitalWrite(motorA1, HIGH);
    digitalWrite(motorA2, LOW);
    // digitalWrite(motorB1, HIGH);
    // digitalWrite(motorB2, LOW);

  } else if (dir == 'F') {
    digitalWrite(motorA1, LOW);
    digitalWrite(motorA2, HIGH);
    // digitalWrite(motorB1, LOW);
    // digitalWrite(motorB2, HIGH);
  } else {
    digitalWrite(motorA1, LOW);
    digitalWrite(motorA2, LOW);
    speed = 0;
  }
  analogWrite(motorAPWM, speed);
  // analogWrite(motorBPWM, speed);
  
  //Serial.println("Command executed: " + command);
  Serial.println("<<ma><complete>>");
}

void handleScaleCommand(String command) {
  if (command.substring(2) == "READ") {
    lcVal = scale.read() + lcTareOff;
    delay(200);
    //Serial.println("HX711 Reading: " + String(lcVal));
    Serial.println("<<lc><"+String(lcVal)+">>");
  } else if (command.substring(2) == "TARE") {
    // long lcSum = 0;
    // int tareInc = 0;
    // while (tareInc < lcTareCount){
    //   lcSum = lcSum + scale.read();
    //   delay(200);
    //   tareInc = tareInc + 1;
    // }
    // lcTareOff = lcSum / lcTareCount;
    scale.tare(5);
    lcTareOff = scale.get_tare();
    Serial.println("<<lc_tare><"+String(lcTareOff)+">>");
  } else if (command.substring(2) == "ALL") {
    lcVal = scale.read() + lcTareOff;
    delay(100);
    //Serial.println("HX711 Reading: " + String(lcVal));
    Serial.println("<<lc><"+String(lcVal)+">>");
    // dispSenseVal = analogRead(dispSensePin);
    // delay(20);
    // Serial.println("<<ds><"+String(dispSenseVal)+">>");
  }
}

void handleLCCommand(String command){
  char dir = command.charAt(2);
  long target = command.substring(3).toInt();
  bool cont = true;
  while (cont == true) {
    handleScaleCommand("HXALL");
    
    if (dir == 'T'){
      handleMotorCommand("MAR200");
      delay(5);
      handleMotorCommand("MAS0");
      if (lcVal >= target){
        cont = false;
        handleMotorCommand("MAS0");
        Serial.println("<<lt><end>>");
      }
    }else if (dir == 'C'){
      handleMotorCommand("MAF200");
      delay(5);
      handleMotorCommand("MAS0");
      if (lcVal <= target){
        cont = false;
        handleMotorCommand("MAS0");
        Serial.println("<<lt><end>>");
      }
    }
  }
}

void handleL2F(String command){
  // Load to Failure cycle
  char dir = command.charAt(2);
  long target = command.substring(3).toInt();
  bool cont = true;
  long prev[3] = {0, 0, 0};
  long cur[3] = {0, 0, 0};
  long avg_prev;
  long avg_cur;
  long change;
  int thresh_change = -50;
  int i = 0;
  bool trig = false;
  long trig_val = 10000;
  long init;
  dir = 'C';
  while (cont == true) {
    handleScaleCommand("HXALL");
    if (i > 0){
      prev[0] = prev[1];
      prev[1] = prev[2];
      prev[2] = cur[0];
      cur[0] = cur[1];
      cur[1] = cur[2];
    } else {
      init = lcVal;
    }
    i += 1;
    
    cur[2] = lcVal;
    avg_prev = (prev[0] + prev[1] + prev[2]) / 3;
    avg_cur = (cur[0] + cur[1] + cur[2]) / 3;
    change = (avg_cur - avg_prev) * 100 / avg_prev;
    if (abs(lcVal) > trig_val && trig == false){
      trig = true;
    }
    if (dir == 'T'){
      handleMotorCommand("MAR255");
      // Set motor ON time based on current load
      if (abs(lcVal) > 750000){
        delay(10);
      } else if (abs(lcVal) > 600000){
        delay(6);
      } else if (abs(lcVal) > 450000){
        delay(4);
      } else {
        delay(2);
      }

      handleMotorCommand("MAS0");
      if (change >= thresh_change && trig == true){
        cont = false;
        handleMotorCommand("MAS0");
        Serial.println("<<lt><end>>");
      }
    }else if (dir == 'C'){
      handleMotorCommand("MAF255");
      // Set motor ON time based on current load
      if (abs(lcVal) > 750000){
        delay(10);
      } else if (abs(lcVal) > 600000){
        delay(6);
      } else if (abs(lcVal) > 400000){
        delay(4);
      } else {
        delay(2);
      }
      handleMotorCommand("MAS0");
      if (change <= thresh_change && trig == true){
        cont = false;
        handleMotorCommand("MAS0");
        Serial.println("<<lt><end>>");
      }
    }
  }
}
