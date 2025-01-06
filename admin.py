import tkinter as tk
from tkinter import messagebox
import socket
import threading
from vidstream import StreamingServer, ScreenShareClient

# Global variables for active stream
connected_senders = []
current_stream_client = None
current_stream_thread = None
stream_lock = threading.Lock()  # Lock to ensure only one stream at a time

# Function to update the list of senders in the GUI
def update_sender_list():
    sender_listbox.delete(0, tk.END)
    for sender in connected_senders:
        sender_listbox.insert(tk.END, sender)

# Function to handle new connections from senders
def listen_for_senders():
    global connected_senders
    listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    listener.bind((receiver_ip, discovery_port))
    while True:
        data, addr = listener.recvfrom(1024)
        sender_ip = addr[0]
        if sender_ip not in connected_senders:
            connected_senders.append(sender_ip)
            update_sender_list()

# Function to request screen sharing from the selected sender
def request_screen_sharing():
    global current_stream_client, current_stream_thread

    selected_index = sender_listbox.curselection()
    if not selected_index:
        return  # No sender selected, so do nothing
    selected_sender = connected_senders[selected_index[0]]

    # Use the lock to ensure only one stream starts/stops at a time
    with stream_lock:
        # Prevent duplicate screen sharing windows
        if current_stream_client and current_stream_thread and current_stream_thread.is_alive():
            print("Screen sharing is already active.")
            return  # Don't start a new stream if one is already active

        # Stop the current stream if any
        if current_stream_client:
            print("Stopping previous stream...")
            current_stream_client.stop_stream()
            current_stream_thread.join()  # Wait for the previous thread to finish
            current_stream_thread = None
            current_stream_client = None

        try:
            # Start screen sharing from the selected sender
            current_stream_client = ScreenShareClient(selected_sender, receiver_port)
            current_stream_thread = threading.Thread(target=current_stream_client.start_stream)
            current_stream_thread.start()
            print(f"Started screen sharing from {selected_sender}")

            # Send a "start" control message to the selected sender
            control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            control_socket.connect((selected_sender, control_port))
            control_socket.sendall(b"start")
            control_socket.close()

        except Exception as e:
            print(f"Failed to connect to {selected_sender}: {e}")

# Function to stop the current stream
def stop_current_stream():
    global current_stream_client, current_stream_thread
    if current_stream_client:
        with stream_lock:
            current_stream_client.stop_stream()
            
            # Only join the thread if it was started
            if current_stream_thread:
                current_stream_thread.join()  # Wait for the stream thread to finish
                current_stream_thread = None  # Ensure the thread is reset
            current_stream_client = None
            messagebox.showinfo("Info", "Screen sharing stopped.")
            
            # Send a "stop" control message to the selected sender
            selected_sender = sender_listbox.get(sender_listbox.curselection())
            control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            control_socket.connect((selected_sender, control_port))
            control_socket.sendall(b"stop")
            control_socket.close()
    else:
        messagebox.showinfo("Info", "No stream to stop.")


# Function to stop server and cleanup threads
def stop_server():
    global current_stream_client
    try:
        if current_stream_client:
            current_stream_client.stop_stream()
            current_stream_thread.join()  # Ensure the current thread is properly joined
            print("Screen sharing stopped.")
        server.stop_server()
        listener_thread.join()  # Ensure the listener thread is properly joined
        print("Server stopped.")
    except Exception as e:
        print(f"Error stopping server: {e}")
    root.quit()

# GUI setup
def setup_gui():
    global sender_listbox
    root = tk.Tk()
    root.title("Screen Sharing Receiver")

    tk.Label(root, text="Connected Senders:").pack()
    sender_listbox = tk.Listbox(root, height=10, width=50)
    sender_listbox.pack()

    request_button = tk.Button(root, text="Request Screen Sharing", command=request_screen_sharing)
    request_button.pack()

    stop_button = tk.Button(root, text="Stop Screen Sharing", command=stop_current_stream)
    stop_button.pack()

    # Ensure stop_server is called when closing the window
    root.protocol("WM_DELETE_WINDOW", stop_server)
    return root

# IP and Port Configurations
receiver_ip = "192.168.0.32"  # Replace with receiver IP
receiver_port = 9999
discovery_port = 8888
control_port = 7777

# Set up the streaming server
server = StreamingServer(receiver_ip, receiver_port)

# Start the server in a separate thread
server_thread = threading.Thread(target=server.start_server)
server_thread.start()

# Start the listener for senders in a separate thread
listener_thread = threading.Thread(target=listen_for_senders)
listener_thread.daemon = True
listener_thread.start()

# Launch the GUI
root = setup_gui()
root.mainloop()
