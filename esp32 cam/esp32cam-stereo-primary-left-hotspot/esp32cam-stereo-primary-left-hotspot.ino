#include <WebServer.h>
#include <WiFi.h>
#include <esp32cam.h>
#include <esp_wifi.h>

const char* AP_SSID = "ESP32_STEREO";
const char* AP_PASS = "stereo1234";

WebServer server(80);
static auto res = esp32cam::Resolution::find(320, 240);

bool secondaryConnected = false;
unsigned long lastConnectionCheck = 0;

void WiFiEvent(WiFiEvent_t event, WiFiEventInfo_t info) {
  switch(event) {
    case ARDUINO_EVENT_WIFI_AP_STACONNECTED:
      Serial.println("Device connected to AP");
      secondaryConnected = true;
      break;
      
    case ARDUINO_EVENT_WIFI_AP_STADISCONNECTED:
      Serial.println("Device disconnected from AP");
      secondaryConnected = false;
      break;
      
    default:
      break;
  }
}

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
    Serial.println(ok ? "Primary CAM OK" : "Primary CAM FAIL");
  }

  WiFi.onEvent(WiFiEvent);
  WiFi.softAP(AP_SSID, AP_PASS);
  
  Serial.print("AP IP: ");
  Serial.println(WiFi.softAPIP());

  WiFi.softAPConfig(
    IPAddress(192, 168, 4, 1),
    IPAddress(192, 168, 4, 1),
    IPAddress(255, 255, 255, 0)
  );

  server.on("/primary.jpg", handlePrimaryJpg);
  server.on("/secondary.jpg", handleSecondaryJpg);
  server.on("/stereo", handleStereo);
  server.on("/status", handleStatus);
  server.begin();
}

void checkConnections() {
  if (millis() - lastConnectionCheck > 5000) {
    lastConnectionCheck = millis();
    
    wifi_sta_list_t stationList;
    esp_wifi_ap_get_sta_list(&stationList);
    
    if (stationList.num > 0) {
      if (!secondaryConnected) {
        Serial.println("Secondary camera connected!");
        secondaryConnected = true;
      }
    } else {
      if (secondaryConnected) {
        Serial.println("Secondary camera disconnected!");
        secondaryConnected = false;
      }
    }
  }
}

void handleStatus() {
  String message = "Primary ESP32-CAM Status\n";
  message += "AP SSID: " + String(AP_SSID) + "\n";
  message += "IP Address: " + WiFi.softAPIP().toString() + "\n";
  message += "Secondary Camera: " + String(secondaryConnected ? "CONNECTED" : "DISCONNECTED") + "\n";
  
  server.send(200, "text/plain", message);
}

void handlePrimaryJpg() {
  serveJpg(true);
}

void handleSecondaryJpg() {
  if (secondaryConnected) {
    server.send(200, "text/plain", "Secondary camera stream would be here");
  } else {
    server.send(503, "text/plain", "Secondary camera not connected");
  }
}

void handleStereo() {
  if (secondaryConnected) {
    String html = "<html><body>";
    html += "<img src='/primary.jpg' width='320' style='float:left'>";
    html += "<img src='/secondary.jpg' width='320'>";
    html += "</body></html>";
    server.send(200, "text/html", html);
  } else {
    server.send(200, "text/plain", "Waiting for secondary camera connection...");
  }
}

void serveJpg(bool isPrimary) {
  auto frame = esp32cam::capture();
  if (frame == nullptr) {
    Serial.println(isPrimary ? "Primary CAPTURE FAIL" : "Secondary CAPTURE FAIL");
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
  checkConnections();
}