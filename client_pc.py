import socket
import cv2
import numpy as np
import mss
import time

def send_screen(host, port):
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # Capture the primary monitor
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))

        try:
            while True:
                # Capture screen
                img = np.array(sct.grab(monitor))

                # Resize the image if necessary (to reduce bandwidth)
                img = cv2.resize(img, (640, 480))

                # Encode the image as MJPEG or JPEG
                _, buffer = cv2.imencode('.jpg', img)  # MJPEG could be used here as well

                # Send image size first (4 bytes), then the image buffer
                size = len(buffer)
                try:
                    sock.sendall(size.to_bytes(4, 'big') + buffer.tobytes())
                except socket.error:
                    print("Error sending data to the server")
                    break

                # Optional: sleep to control the frame rate (e.g., 30fps)
                time.sleep(1 / 30)  # 30 FPS rate
        except Exception as e:
            print(f"Error during capture or transmission: {e}")
        finally:
            sock.close()

# Replace with the admin PC's IP and desired port

send_screen('192.168.0.241', 5000)
