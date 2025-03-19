"""
Summary:
Simple AirDrop-like sender (client) for sending files to another machine securely.

Instructions:
Before using, you have to run "keygen.py".

Copy the key you were given, including the b. Replace "enter code" below with it.

"""
import socket
from cryptography.fernet import Fernet
import tkinter.filedialog as fd
import os
import traceback

# Hard-coded Fernet key
key = "enter code"  # Replace with your generated key
fernet = Fernet(key)

def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception as e:
        print(f"Error getting local IP address: {e}")
        return None

def send_file(conn, filename):
    with open(filename, 'rb') as f:
        file_data = f.read()
        encrypted_data = fernet.encrypt(file_data)
        print(f"Sending file: {filename}")
        conn.sendall(encrypted_data)
    print(f"Finished sending file: {filename}")

def main():
    server_ip = get_local_ip()
    if not server_ip:
        print("Could not determine server's local IP address. Exiting.")
        return

    print(f"Server's local IP address: {server_ip}")

    port = 6000
    filename = fd.askopenfilename(title="Select a file to send")
    if not filename:
        print("No file selected. Exiting.")
        return

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((server_ip, port))  # Connect to the server
            # Use utf-8 encoding to handle filenames with special characters
            s.sendall((os.path.basename(filename) + '\n').encode('utf-8'))  # Encode file basename and send via secure connection to server
            send_file(s, filename)  # Send contents of file via secure connection to server.
        except Exception as e:
            print(f"Error connecting to server: {e}")

if __name__ == "__main__":
    main()