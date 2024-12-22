import sys
import socket
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QComboBox
from PyQt5.QtGui import QImage, QPixmap, QIcon
import subprocess
import platform
import ipaddress

class ScreenViewer(QWidget):
    def __init__(self, port):
        super().__init__()
        self.port = port
        self.device_ips = []  # List to store available devices
        self.current_conn = None  # Store the current connection

        self.init_ui()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('', self.port))
        self.sock.listen(5)

    def init_ui(self):
        """ Initialize the UI components """
        self.setWindowTitle("Admin Viewer")
        self.setGeometry(100, 100, 400, 400)  # Set window size to 400x400
        self.layout = QVBoxLayout()

        # Device selection combo box
        self.device_selector = QComboBox(self)
        self.device_selector.setPlaceholderText("Select Device")
        self.device_selector.currentIndexChanged.connect(self.on_device_selected)
        self.layout.addWidget(self.device_selector)

        # Image display label
        self.image_label = QLabel(self)
        self.layout.addWidget(self.image_label)

        self.setWindowIcon(QIcon('icon.jpg'))  # Replace with your icon file
        self.setLayout(self.layout)

    def on_device_selected(self):
        """ Handle device selection """
        selected_ip = self.device_selector.currentText()
        if selected_ip and self.is_valid_ip(selected_ip):
            self.connect_to_device(selected_ip)
        else:
            print(f"Invalid or empty IP selected: {selected_ip}")

    def connect_to_device(self, ip):
        """ Connect to the selected device and start receiving video stream """
        if self.current_conn:
            self.current_conn.close()

        self.current_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            print(f"Connecting to {ip} on port {self.port}...")
            self.current_conn.connect((ip, self.port))
            self.start_receiving()
        except Exception as e:
            print(f"Error connecting to {ip}: {e}")

    def start_receiving(self):
        """ Receive and display screen data """
        if self.current_conn is None:
            return

        while True:
            size_data = self.current_conn.recv(4)
            if not size_data:
                break
            size = int.from_bytes(size_data, 'big')

            buffer = b''
            while len(buffer) < size:
                buffer += self.current_conn.recv(size - len(buffer))

            img = cv2.imdecode(np.frombuffer(buffer, dtype=np.uint8), cv2.IMREAD_COLOR)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            height, width, channel = img.shape
            bytes_per_line = channel * width
            q_image = QImage(img.data, width, height, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)

            self.image_label.setPixmap(pixmap)

    def discover_devices(self):
        """ Discover available devices running the client script """
        self.device_ips = self.ping_sweep("192.168.0")  # Change to 192.168.0 subnet
        self.device_selector.clear()
        self.device_selector.addItem("Select Device")
        self.device_selector.addItems(self.device_ips)

    def ping_sweep(self, subnet):
        """ Ping devices in the subnet and return a list of reachable IPs """
        reachable_ips = []
        for i in range(1, 255):
            ip = f"{subnet}.{i}"
            if self.ping_ip(ip):
                reachable_ips.append(ip)
        return reachable_ips

    def ping_ip(self, ip):
        """ Check if the IP is reachable via ping """
        try:
            param = "-n" if platform.system().lower() == "windows" else "-c"
            response = subprocess.run(
                ['ping', param, '1', '-W', '1', ip],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return response.returncode == 0
        except Exception:
            return False

    def is_valid_ip(self, ip):
        """ Validate the IP address format """
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = ScreenViewer(5000)
    viewer.show()

    # Discover devices before the user selects
    viewer.discover_devices()

    sys.exit(app.exec_())
