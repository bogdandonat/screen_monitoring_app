import socket
from vidstream import ScreenShareClient
import threading
import time

# Declare client as a global variable
client = None
client_thread = None

# Function to start screen sharing
def start_screen_sharing():
    global client, client_thread
    if client is not None:
        print("Screen sharing is already running.")
        return  # Don't start a new stream if one is already active

    client = ScreenShareClient(receiver_ip, receiver_port)
    client_thread = threading.Thread(target=client.start_stream)
    client_thread.start()
    print("Screen sharing started.")

# Listen for incoming control requests (start/stop)
def listen_for_control_requests():
    global client  # Make sure to use the global client variable
    control_listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    control_listener.bind(("0.0.0.0", control_port))  # Bind to all available IPs
    control_listener.listen(1)
    while True:
        try:
            conn, addr = control_listener.accept()
            request = conn.recv(1024).decode('utf-8')
            if request == "start":
                print(f"Received start request from {addr}")
                start_screen_sharing()
            elif request == "stop":
                if client:  # Check if client exists before calling stop
                    client.stop_stream()
                    print(f"Received stop request from {addr}")
                client = None  # Reset the client after stopping
        except KeyboardInterrupt:
            print("Shutting down server...")
            break  # Exit the loop when KeyboardInterrupt is caught
    control_listener.close()

# IP and Port Configurations
receiver_ip = "192.168.0.32"  # Replace with receiver's IP address
receiver_port = 9999
control_port = 7777
discovery_port = 8888

# Start listening for control requests in a separate thread
control_thread = threading.Thread(target=listen_for_control_requests)
control_thread.daemon = True
control_thread.start()

# Announce sender availability to the receiver periodically
def announce_to_receiver():
    while True:
        try:
            discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            discovery_socket.sendto(b"hello", (receiver_ip, discovery_port))
            discovery_socket.close()
            time.sleep(5)  # Announce every 5 seconds
        except KeyboardInterrupt:
            print("Announce thread interrupted. Exiting...")
            break  # Exit the loop when KeyboardInterrupt is caught

# Start announcing availability
announce_thread = threading.Thread(target=announce_to_receiver)
announce_thread.daemon = True
announce_thread.start()

# Keep the sender running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Client stopped. Shutting down...")
    if client:
        client.stop_stream()  # Stop the screen sharing if it's running
    # Clean up and close any open sockets, threads, etc.
    if client_thread:
        client_thread.join()  # Wait for the thread to finish
    print("Exiting the program.")
