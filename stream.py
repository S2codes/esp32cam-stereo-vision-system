from flask import Flask, Response, render_template
import cv2
import urllib.request
import numpy as np
import threading
import time
from datetime import datetime

app = Flask(__name__)

# ESP32-CAM URLs
PRIMARY_URL = 'http://192.168.4.1/primary.jpg'  # Primary ESP32 (access point)
SECONDARY_URL = 'http://192.168.4.2/secondary.jpg'  # Secondary ESP32

# Global variables for frame storage
latest_primary_frame = None
latest_secondary_frame = None
frame_lock = threading.Lock()
recording = False
out = None

def fetch_frames():
    global latest_primary_frame, latest_secondary_frame, recording
    
    while True:
        try:
            # Fetch primary camera frame
            primary_resp = urllib.request.urlopen(PRIMARY_URL, timeout=2)
            primary_np = np.array(bytearray(primary_resp.read()), dtype=np.uint8)
            primary_frame = cv2.imdecode(primary_np, cv2.IMREAD_COLOR)
            
            # Fetch secondary camera frame
            secondary_resp = urllib.request.urlopen(SECONDARY_URL, timeout=2)
            secondary_np = np.array(bytearray(secondary_resp.read()), dtype=np.uint8)
            secondary_frame = cv2.imdecode(secondary_np, cv2.IMREAD_COLOR)
            
            with frame_lock:
                latest_primary_frame = primary_frame
                latest_secondary_frame = secondary_frame
                
                # If recording, write frames to video file
                if recording and out is not None:
                    # Combine frames side-by-side
                    stereo_frame = np.hstack((primary_frame, secondary_frame))
                    out.write(stereo_frame)
                    
        except Exception as e:
            print(f"Error fetching frames: {e}")
            time.sleep(1)

def generate_frames():
    while True:
        with frame_lock:
            if latest_primary_frame is not None and latest_secondary_frame is not None:
                # Create stereo view (side-by-side)
                stereo_frame = np.hstack((latest_primary_frame, latest_secondary_frame))
                
                # Process frame if needed (add your processing here)
                # processed_frame = process_frame(stereo_frame)
                processed_frame = stereo_frame
                
                # Encode as JPEG
                ret, buffer = cv2.imencode('.jpg', processed_frame)
                frame = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                time.sleep(0.1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/start_recording')
def start_recording():
    global recording, out
    if not recording:
        recording = True
        # Create video writer
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_path = f'stereo_recording_{timestamp}.avi'
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(video_path, fourcc, 10.0, (640, 240))  # 320x240 x2
        return f"Recording started: {video_path}"
    return "Already recording"

@app.route('/stop_recording')
def stop_recording():
    global recording, out
    if recording:
        recording = False
        out.release()
        out = None
        return "Recording stopped"
    return "No active recording"

if __name__ == '__main__':
    # Start frame fetching thread
    threading.Thread(target=fetch_frames, daemon=True).start()
    
    # Start Flask app
    app.run(host='0.0.0.0', port=5000, threaded=True)