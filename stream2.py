from flask import Flask, Response, render_template
import cv2
import urllib.request
import numpy as np
import threading
import time
from datetime import datetime
import os

app = Flask(__name__)

# ESP32-CAM URLs
PRIMARY_URL = 'http://192.168.4.1/primary.jpg'  # Primary ESP32 (access point)
SECONDARY_URL = 'http://192.168.4.2/secondary.jpg'  # Secondary ESP32

# Global variables for frame storage
latest_primary_frame = None
latest_secondary_frame = None
frame_lock = threading.Lock()
recording = False
stereo_out = None
left_out = None
right_out = None
recording_dir = 'recordings'

def ensure_recording_dir():
    if not os.path.exists(recording_dir):
        os.makedirs(recording_dir)

def fetch_frames():
    global latest_primary_frame, latest_secondary_frame, recording
    global stereo_out, left_out, right_out
    
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
                
                # If recording, write frames to all video files
                if recording:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    # Combine frames side-by-side for stereo view
                    stereo_frame = np.hstack((primary_frame, secondary_frame))
                    stereo_out.write(stereo_frame)
                    
                    # Write individual camera frames
                    left_out.write(primary_frame)
                    right_out.write(secondary_frame)
                    
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
    global recording, stereo_out, left_out, right_out
    if not recording:
        ensure_recording_dir()
        recording = True
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Video parameters (adjust based on your camera resolution)
        frame_width = 320
        frame_height = 240
        fps = 10
        
        # Create video writers for all three videos
        stereo_path = os.path.join(recording_dir, f'stereo_{timestamp}.mp4')
        left_path = os.path.join(recording_dir, f'left_{timestamp}.mp4')
        right_path = os.path.join(recording_dir, f'right_{timestamp}.mp4')
        
        # Use MP4V codec for MP4 files
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        
        # Stereo view (side-by-side) - double width
        stereo_out = cv2.VideoWriter(stereo_path, fourcc, fps, (frame_width*2, frame_height))
        
        # Individual camera views
        left_out = cv2.VideoWriter(left_path, fourcc, fps, (frame_width, frame_height))
        right_out = cv2.VideoWriter(right_path, fourcc, fps, (frame_width, frame_height))
        
        return f"Recording started:<br>Stereo: stereo_{timestamp}.mp4<br>Left: left_{timestamp}.mp4<br>Right: right_{timestamp}.mp4"
    return "Already recording"

@app.route('/stop_recording')
def stop_recording():
    global recording, stereo_out, left_out, right_out
    if recording:
        recording = False
        stereo_out.release()
        left_out.release()
        right_out.release()
        stereo_out = None
        left_out = None
        right_out = None
        return "Recording stopped and files saved"
    return "No active recording"

if __name__ == '__main__':
    # Start frame fetching thread
    threading.Thread(target=fetch_frames, daemon=True).start()
    
    # Start Flask app
    app.run(host='0.0.0.0', port=5000, threaded=True)