// ESP32 as wifi
#include <WiFi.h>
#include <esp32cam.h>
#include <WebServer.h>

const char* PRIMARY_SSID = "ESP32_STEREO";
const char* PRIMARY_PASS = "stereo1234";

WebServer server(80);
static auto res = esp32cam::Resolution::find(320, 240);

void setup() {
  Serial.begin(115200);
  
  // Initialize camera
  {
    using namespace esp32cam;
    Config cfg;
    cfg.setPins(pins::AiThinker);
    cfg.setResolution(res);
    cfg.setBufferCount(2);
    cfg.setJpeg(80);
    
    bool ok = Camera.begin(cfg);
    Serial.println(ok ? "Secondary CAM OK" : "Secondary CAM FAIL");
  }

  // Connect to primary ESP32's AP
  WiFi.begin(PRIMARY_SSID, PRIMARY_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.print("Connected. IP: ");
  Serial.println(WiFi.localIP());

  server.on("/secondary.jpg", handleJpg);
  server.begin();
}

void handleJpg() {
  auto frame = esp32cam::capture();
  if (frame == nullptr) {
    server.send(503, "", "");
    return;
  }
  
  server.setContentLength(frame->size());
  server.send(200, "image/jpeg");
  WiFiClient client = server.client();
  frame->writeTo(client);
}

void loop() {
  server.handleClient();
}