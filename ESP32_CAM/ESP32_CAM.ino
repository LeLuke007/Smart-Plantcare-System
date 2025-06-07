#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>

const char* ssid = ""; // Your Wi-Fi SSID
const char* password = ""; // Your Wi-Fi Password

WebServer server(80);

// Camera pin definitions for AI-Thinker module
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM       5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

void handleCapture() {
  camera_fb_t * fb = esp_camera_fb_get();
  if(!fb) {
    server.send(500, "text/plain", "Camera capture failed");
    return;
  }
  server.send_P(200, "image/jpeg", (const char*)fb->buf, fb->len);
  esp_camera_fb_return(fb);
}

void setup(){
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(100);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("Camera ready at http://");
  Serial.println(WiFi.localIP());

  pinMode(4,OUTPUT);
  digitalWrite(4,HIGH);
  delay(2000);
  digitalWrite(4,LOW);

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0       = Y2_GPIO_NUM;
  config.pin_d1       = Y3_GPIO_NUM;
  config.pin_d2       = Y4_GPIO_NUM;
  config.pin_d3       = Y5_GPIO_NUM;
  config.pin_d4       = Y6_GPIO_NUM;
  config.pin_d5       = Y7_GPIO_NUM;
  config.pin_d6       = Y8_GPIO_NUM;
  config.pin_d7       = Y9_GPIO_NUM;
  config.pin_xclk     = XCLK_GPIO_NUM;
  config.pin_pclk     = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM;
  config.pin_href     = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn     = PWDN_GPIO_NUM;
  config.pin_reset    = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size   = FRAMESIZE_SVGA;
  config.fb_location  = CAMERA_FB_IN_DRAM;
  config.jpeg_quality = 36;  // 0 = best, 63 = worst
  config.fb_count     = 1;

  if (esp_camera_init(&config) != ESP_OK) {
    Serial.println("Camera init failed");
    return;
  }

  // Route /capture to handleCapture()
  server.on("/capture", HTTP_GET, handleCapture);
  server.on("/flashon", HTTP_GET, handleFlashOn);
  server.on("/flashoff", HTTP_GET, handleFlashOff);
  server.begin();
}

void loop(){
  server.handleClient();
}

void handleFlashOn() {
  digitalWrite(4, HIGH);
  server.send(200, "text/plain", "Flash ON");
}

void handleFlashOff() {
  digitalWrite(4, LOW);
  server.send(200, "text/plain", "Flash OFF");
}