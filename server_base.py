"""
Summary: Reciever to pair wih the sender.

Instructions:
Replace "your key" below with the same key used in your sender. Share the updated "sender_base.py" and "server_base.py" to people you want to allow to send/recieve files from.

"""
import socket
import os
import threading
from cryptography.fernet import Fernet
import traceback

# Hard-coded Fernet key
key = "your key"  # Replace with your generated key
fernet = Fernet(key)

TEMP_DIR = os.path.join(os.path.expanduser("~"), "Documents", "AirDropped Files")
os.makedirs(TEMP_DIR, exist_ok=True)

def receive_file(conn, filename):
    file_data = b""
    while True:
        data = conn.recv(1024)
        if not data:
            break
        file_data += data

    if not file_data:
        print(f"No data received for file: {filename}")
        return

    try:
        decrypted_data = fernet.decrypt(file_data)
        file_path = os.path.join(TEMP_DIR, filename)
        with open(file_path, "wb") as f:
            f.write(decrypted_data)
        print(f"Received and decrypted file: {filename}")
    except Exception as e:
        print(f"Decryption error: {e}")
        traceback.print_exc()

def handle_client(conn, addr):
    print(f"Connected by {addr}")
    try:
        # Use utf-8 encoding to handle filenames with special characters
        filename_data = b""
        while True:
            data = conn.recv(1024)
            if not data:
                print(f"Received no data from {addr}. Closing connection.")
                conn.close()
                return
            filename_data += data
            if b'\n' in filename_data:  # Assuming filename is terminated by a newline character
                filename = filename_data.decode('utf-8').strip()
                break
        
        if not filename:
            print(f"Received empty filename from {addr}. Closing connection.")
            conn.close()
            return
        print(f"Receiving file: {filename}")
        receive_file(conn, filename)
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
        traceback.print_exc()  # Print the stack trace for more details
    finally:
        conn.close()

def main():
    host = '0.0.0.0'  # Listen on all interfaces
    port = 6000  # Port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))  # Bind host and port
        s.listen()  # Begin listening to socket for transmissions
        print(f"Listening on {host}:{port}")  # Confirm reading
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    main()