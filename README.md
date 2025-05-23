# 🎥 ESP32-CAM Stereo Vision System

A complete solution for capturing and streaming stereo video using two ESP32-CAM modules, with recording capabilities via a Python web interface.



## 📋 Project Structure

```
esp32cam-stereo/
├── primary/                 # Left camera (Access Point)
│   └── esp32cam_primary.ino
├── secondary/               # Right camera (WiFi Client)
│   └── esp32cam_secondary.ino
├── stream_server/           # Python streaming server
│   ├── stream.py
│   └── templates/
│       └── index.html
└── README.md
```

## 🌟 Key Features

- **Dual Camera Streaming**: Simultaneous capture from two ESP32-CAM modules
- **Hotspot Mode**: Primary camera creates its own WiFi network
- **Stereo Web Viewer**: Side-by-side video display with recording
- **Connection Monitoring**: Automatic detection of secondary camera
- **Simple Web UI**: Start/stop recording with one click

## 🛠 Hardware Requirements

| Component | Quantity | Notes |
|-----------|----------|-------|
| ESP32-CAM (AI-Thinker) | 2 | Main camera modules |
| Micro USB cable | 2 | For power and programming |
| FTDI Programmer | 1 | For flashing firmware |
| **Optional**: SD Card | 1-2 | For local recording |

## 🔌 Wiring Guide

For each ESP32-CAM:

| ESP32-CAM | FTDI Programmer |
|-----------|-----------------|
| GPIO0 | GND (during programming) |
| GND | GND |
| 5V/VCC | 5V |
| U0R | TXD |
| U0T | RXD |

## ⚙️ Software Setup

### 1. Primary Camera (Access Point)
```arduino
// Creates hotspot "ESP32_STEREO" at 192.168.4.1
// Endpoints:
// - /primary.jpg       : Left camera feed
// - /status            : System status
// - /stereo            : Stereo view page
```

### 2. Secondary Camera (WiFi Client)
```arduino
// Connects to primary's hotspot
// Provides:
// - /secondary.jpg     : Right camera feed
```

### 3. Python Streaming Server
```bash
# Install dependencies
pip install flask opencv-python numpy

# Run server
python stream.py
```

Access at: **http://localhost:5000**

## 🌐 Web Interface

**Controls:**

- ▶️ **Start Recording**: Saves video as `stereo_recording_TIMESTAMP.avi`
- ⏹ **Stop Recording**: Ends current recording
- 🔄 Auto-refreshing stereo view

## 📡 Network Configuration

| Parameter | Value |
|-----------|-------|
| Hotspot SSID | ESP32_STEREO |
| Hotspot Password | stereo1234 |
| Primary IP | 192.168.4.1 |
| Secondary IP | 192.168.4.2 (DHCP) |
| Stream Server | http://localhost:5000 |

## 🚀 Deployment Guide

1. Flash both ESP32-CAM modules with their respective code
2. Power the primary camera first (creates hotspot)
3. Power the secondary camera (auto-connects)
4. Run the Python server on your computer
5. Connect computer to ESP32_STEREO network
6. Access http://localhost:5000

## 🛠 Troubleshooting

| Issue | Solution |
|-------|----------|
| **Cameras not connecting** | ✅ Verify both use same WiFi credentials<br>✅ Check serial monitor for connection status |
| **Poor video quality** | ✅ Reduce resolution in `esp32cam::Resolution::find()`<br>✅ Move cameras closer to router |
| **Recording lag** | ✅ Lower FPS in `cv2.VideoWriter()`<br>✅ Use wired connection if possible |

## 📚 Documentation Reference

### Primary Camera Endpoints
| Endpoint | Description |
|----------|-------------|
| /primary.jpg | Left camera JPEG stream |
| /secondary.jpg | Right camera proxy |
| /stereo | Stereo HTML view |
| /status | Connection status |

### Secondary Camera Endpoints
| Endpoint | Description |
|----------|-------------|
| /secondary.jpg | Right camera JPEG stream |

## 🤝 Contributing

Pull requests welcome! Key areas for improvement:

- Add depth map generation
- Implement motion detection
- Improve frame synchronization