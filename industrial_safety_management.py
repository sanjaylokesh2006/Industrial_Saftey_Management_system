import os
import urllib.request
import cv2
import numpy as np
import time
import pygame
import sys
from pygame import mixer
from datetime import datetime

class IndustrialSafetyMonitor:
    def __init__(self):
        # Initialize audio system first (needs to happen before other pygame stuff)
        self.initialize_audio_system()

        # Download required model files if they don't exist
        self.download_model_files()

        # Initialize face detection model
        try:
            self.face_net = cv2.dnn.readNetFromCaffe(
                "deploy.prototxt",
                "res10_300x300_ssd_iter_140000.caffemodel"
            )
            self.confidence_threshold = 0.7  # 70% confidence threshold
            self.machine_running = False
            self.alert_active = False
        except Exception as e:
            self.log_message(f"Failed to initialize face detection model: {e}")
            self.clean_exit()

    def log_message(self, message):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")

    def initialize_audio_system(self):
        """Initialize pygame mixer with reliable settings"""
        try:
            pygame.init()
            mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
            self.generate_beep_sound(880, 0.3)  # 880Hz beep for 0.3 seconds
            self.log_message("Audio system initialized successfully")
        except Exception as e:
            self.log_message(f"Audio initialization failed: {e}")
            self.alert_sound = None

    def generate_beep_sound(self, frequency, duration):
        """Generate a proper beep sound"""
        try:
            sample_rate = 44100
            samples = (0.7 * 32767 * np.sin(
                2 * np.pi * np.arange(sample_rate * duration) *
                frequency / sample_rate)).astype(np.int16)
            stereo_samples = np.column_stack((samples, samples))
            self.alert_sound = mixer.Sound(buffer=stereo_samples)
        except Exception as e:
            self.log_message(f"Couldn't generate beep sound: {e}")
            self.alert_sound = None

    def download_model_files(self):
        """Download required OpenCV model files if missing"""
        models = {
            "deploy.prototxt": "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt",
            "res10_300x300_ssd_iter_140000.caffemodel": "https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel"
        }

        for filename, url in models.items():
            if not os.path.exists(filename):
                self.log_message(f"Downloading {filename}...")
                try:
                    urllib.request.urlretrieve(url, filename)
                except Exception as e:
                    self.log_message(f"Failed to download {filename}: {e}")
                    self.clean_exit()

    def set_machine_state(self, running):
        """Control machine operational state"""
        self.machine_running = running
        status = "STARTED" if running else "STOPPED"
        self.log_message(f"Machine {status}")

    def process_frame(self, frame):
        """Analyze frame for faces and trigger safety protocols"""
        if not self.machine_running:
            return frame, False

        (h, w) = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame, (300, 300)), 1.0,
            (300, 300), (104.0, 177.0, 123.0)
        )

        self.face_net.setInput(blob)
        detections = self.face_net.forward()

        face_detected = False

        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > self.confidence_threshold:
                face_detected = True
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")

                # Visual indication with timestamp
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 0, 255), 2)
                cv2.putText(frame, f"INTRUDER: {confidence*100:.1f}% @ {timestamp}",
                           (startX, startY - 10), cv2.FONT_HERSHEY_SIMPLEX,
                           0.45, (0, 0, 255), 2)

                # Safety protocols
                if not self.alert_active:
                    self.trigger_safety_protocols()
                break

        return frame, face_detected

    def trigger_safety_protocols(self):
        """Execute all safety measures when intrusion detected"""
        self.alert_active = True
        self.set_machine_state(False)

        # Visual alert with timestamp
        self.show_visual_alert()

        # Audio alert
        self.play_alert_sound()

        # System notification
        self.log_message("!!! SAFETY ALERT !!!")
        self.log_message("Person detected in restricted area!")
        self.log_message("Machine has been stopped automatically")

        self.alert_active = False

    def show_visual_alert(self):
        """Display flashing visual warning with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for _ in range(3):  # Flash 3 times
            # Red alert
            alert_img = np.zeros((200, 800, 3), np.uint8)
            alert_img[:] = (0, 0, 255)
            cv2.putText(alert_img, f"SAFETY ALERT @ {timestamp}",
                       (50, 100), cv2.FONT_HERSHEY_SIMPLEX,
                       0.9, (255, 255, 255), 2)
            cv2.imshow("SAFETY ALERT", alert_img)
            cv2.waitKey(300)

            # White alert
            alert_img[:] = (255, 255, 255)
            cv2.putText(alert_img, f"SAFETY ALERT @ {timestamp}",
                       (50, 100), cv2.FONT_HERSHEY_SIMPLEX,
                       0.9, (0, 0, 255), 2)
            cv2.imshow("SAFETY ALERT", alert_img)
            cv2.waitKey(300)

    def play_alert_sound(self):
        """Play attention-grabbing alarm sound"""
        if self.alert_sound:
            try:
                for _ in range(3):  # Triple beep
                    self.alert_sound.play()
                    while mixer.get_busy():  # Wait for completion
                        time.sleep(0.05)
                    time.sleep(0.15)  # Short pause between beeps
            except Exception as e:
                self.log_message(f"Audio alert error: {e}")

    def clean_exit(self):
        """Proper system shutdown"""
        pygame.quit()
        sys.exit(1)

def main():
    # Initialize system with timestamp
    startup_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{startup_time}] === INDUSTRIAL SAFETY MONITOR ===")
    print(f"[{startup_time}] SAFETY PROTOCOLS:")
    print(f"[{startup_time}]  - Automatic machine shutdown when person detected")
    print(f"[{startup_time}]  - Visual and audio alarms activated")
    print(f"[{startup_time}] CONTROLS:")
    print(f"[{startup_time}]  s - Start machine monitoring")
    print(f"[{startup_time}]  x - Stop machine")
    print(f"[{startup_time}]  q - Quit system\n")

    # Initialize system
    safety_system = IndustrialSafetyMonitor()

    # Camera setup
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise RuntimeError("Cannot open camera")
    except Exception as e:
        safety_system.log_message(f"Camera error: {e}")
        safety_system.clean_exit()

    # Main monitoring loop
    while True:
        ret, frame = cap.read()
        if not ret:
            safety_system.log_message("Camera feed error")
            break

        # Safety monitoring
        processed_frame, _ = safety_system.process_frame(frame)
        cv2.imshow("Safety Monitor", processed_frame)

        # Control handling
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            safety_system.set_machine_state(True)
        elif key == ord('x'):
            safety_system.set_machine_state(False)

    # Clean shutdown
    cap.release()
    cv2.destroyAllWindows()
    pygame.quit()
    shutdown_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{shutdown_time}] Safety system shutdown complete")

if __name__ == "__main__":
    main()