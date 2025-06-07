#include <Arduino.h>
#include <WiFi.h>
#include <ESPAsyncWebServer.h>
#include <DHT.h>
#include <ESP32Servo.h>

#define SOIL_POWER_PIN 13
#define SOIL_ADC_PIN 34
#define PUMP_PIN 12
#define DHT22_PIN 32
#define DHT22_POWER 14
#define FAN_PIN 27
#define LDR_PIN 33
#define LDR_POWER 26
#define MOTOR_L 15
//#define MOTOR_R 5

unsigned long timeoutTime = 5000;
unsigned long ldrLowStart = 0;
unsigned long ldrHighStart = 0;
bool isOpen = false;

int soil_mositure_threshold = 55;
float temp_threshold = 27.5;
float hum_threshold = 75;

DHT dht22(DHT22_PIN, DHT22);
Servo servo1;

const char* ssid = ""; // Your Wi-Fi SSID
const char* pass = ""; // Your Wi-Fi Password

AsyncWebServer server(80);

// State Variables
String mode = "auto"; // "auto" or "manual"
bool manualPumpOn = false;
bool manualFanOn = false;
bool manualRoofOn = false;

void setup() {
  Serial.begin(115200);

  WiFi.begin(ssid, pass);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWi-Fi connected");
  Serial.println(WiFi.localIP());

  dht22.begin();
  servo1.attach(MOTOR_L);
  servo1.write(0);

  pinMode(SOIL_POWER_PIN, OUTPUT);
  pinMode(PUMP_PIN, OUTPUT);
  pinMode(DHT22_POWER, OUTPUT);
  pinMode(FAN_PIN, OUTPUT);
  pinMode(LDR_POWER, OUTPUT);

  pinMode(LDR_PIN, INPUT);

  digitalWrite(SOIL_POWER_PIN, HIGH);
  digitalWrite(PUMP_PIN, LOW);
  digitalWrite(FAN_PIN, LOW);
  digitalWrite(DHT22_POWER, HIGH);
  digitalWrite(LDR_POWER, HIGH);

  server.on("/", HTTP_GET, [](AsyncWebServerRequest *req){
    req->send(200, "text/html", "ESP32 Server Running");
  });

  server.on("/sensor", HTTP_GET, [](AsyncWebServerRequest *req){
    int val = readSensor();
    req->send(200, "text/plain", String(val));
  });

  server.on("/dht", HTTP_GET, [](AsyncWebServerRequest *req){
    float h, t;
    readDHT(h, t);
    String data = String(h) + "," + String(t);
    req->send(200, "text/plain", data);
  });

  server.on("/ldr", HTTP_GET, [](AsyncWebServerRequest *req){
    int ldr;
    readLDR(ldr);
    req->send(200, "text/plain", String(ldr));
  });

  server.on("/setmode", HTTP_GET, [](AsyncWebServerRequest *req){
    if (req->hasParam("mode")) {
      mode = req->getParam("mode")->value();
      Serial.println("Mode set to: " + mode);
    }
    req->send(200, "text/plain", mode);
  });

  server.on("/manualpump", HTTP_GET, [](AsyncWebServerRequest *req){
    if (mode == "manual" && req->hasParam("state")) {
      String state = req->getParam("state")->value();
      manualPumpOn = (state == "on");
      digitalWrite(PUMP_PIN, manualPumpOn ? LOW : HIGH);
      Serial.println("Manual Pump State: " + state);
      req->send(200, "text/plain", "Pump " + state);
    } else {
      req->send(400, "text/plain", "Manual mode not active or invalid request");
    }
  });

  server.on("/manualfan", HTTP_GET, [](AsyncWebServerRequest *req){
    if (mode == "manual" && req->hasParam("state")) {
      String state = req->getParam("state")->value();
      manualFanOn = (state == "on");
      digitalWrite(FAN_PIN, manualFanOn ? LOW : HIGH);
      Serial.println("Manual Fan State: " + state);
      req->send(200, "text/plain", "Fan " + state);
    } else {
      req->send(400, "text/plain", "Manual mode not active or invalid request");
    }
  });

  server.on("/manualroof", HTTP_GET, [](AsyncWebServerRequest *req){
    if (mode == "manual" && req->hasParam("state")) {
      String state = req->getParam("state")->value();
      manualRoofOn = (state == "open");
      if (state == "open" && !isOpen){
        motor_open();
        isOpen = true;
      }
      if (state == "close" && isOpen){
        motor_close();
        isOpen = false;
      }
      Serial.println("Manual Roof State: " + state);
      req->send(200, "text/plain", "Roof " + state);
    } else {
      req->send(400, "text/plain", "Manual mode not active or invalid request");
    }
  });

  server.on("/setthresholds", HTTP_GET, [](AsyncWebServerRequest *req){
    if(req->hasParam("soil"))  soil_mositure_threshold = req->getParam("soil")->value().toInt();
    if(req->hasParam("temp"))  temp_threshold = req->getParam("temp")->value().toFloat();
    if(req->hasParam("hum"))   hum_threshold  = req->getParam("hum")->value().toFloat();
    req->send(200,"application/json",
      "{\"soil\":"+String(soil_mositure_threshold)+
      ",\"temp\":"+String(temp_threshold)+
      ",\"hum\":"+String(hum_threshold)+"}");
  });

  server.begin();
}

void loop() {
  if (mode == "auto") {
    int moisture = readSensor();
    digitalWrite(PUMP_PIN, moisture <= soil_mositure_threshold ? LOW : HIGH);

    float h, t;
    readDHT(h, t);
    digitalWrite(FAN_PIN, (t > temp_threshold || h > hum_threshold) ? LOW : HIGH);

    int ldr;
    readLDR(ldr);
    motor_control(ldr);
  }
  //delay(1000);
}

int readSensor() {
  //digitalWrite(SOIL_POWER_PIN, HIGH);
  //delay(10);
  int v = analogRead(SOIL_ADC_PIN);
  //digitalWrite(SOIL_POWER_PIN, LOW);
  int moisture = (100 - ((v / 4095.00) * 100));
  Serial.print("Soil Moisture: "); Serial.print(moisture); Serial.println("%");
  return moisture;
}

void readDHT(float &humi, float &tempC){
  humi  = dht22.readHumidity();
  tempC = dht22.readTemperature();
  if (isnan(tempC) || isnan(humi)) {
    Serial.println("Failed to read from DHT22 sensor!");
  } else {
    Serial.print("Humidity: "); Serial.print(humi); Serial.print("%  |  ");
    Serial.print("Temperature: "); Serial.println(tempC);
  }
}

void readLDR(int &op){
  op = digitalRead(LDR_PIN);
  Serial.print("LDR Value = "); Serial.println(op);
}

void motor_control(int ldrVal){
  unsigned long currentTime = millis();

  if (ldrVal == 0) {
    if (ldrLowStart == 0) ldrLowStart = currentTime;
    ldrHighStart = 0;

    if (!isOpen && currentTime - ldrLowStart >= timeoutTime) {
      motor_open();
      isOpen = true;
    }
  }
  else {
    if (ldrHighStart == 0) ldrHighStart = currentTime;
    ldrLowStart = 0;

    if (isOpen && currentTime - ldrHighStart >= timeoutTime) {
      motor_close();
      isOpen = false;
    }
  }
}

void motor_open(){
  Serial.println("Opening Roof");
  for (int pos=0; pos<=90; pos+=1){
    servo1.write(pos);
    delay(50);
  }
}

void motor_close(){ 
  Serial.println("Closing Roof");
  for (int pos=90; pos>=0; pos-=1) {
    servo1.write(pos);
    delay(20);
  }
}
