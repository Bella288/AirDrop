"""
Summary:
Simple AirDrop-like sender (client) for sending files to another machine securely.

Instructions:
Before using, you have to run "keygen.py".

Copy the key you were given, including the b. Replace "enter code" below with it.

"""
import os
import threading
import socket
from cryptography.fernet import Fernet
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from twisted.internet import reactor, protocol, endpoints
from zeroconf import ServiceBrowser, Zeroconf, ServiceStateChange

# Hard-coded Fernet key
key = enter code  # Replace with your generated key
fernet = Fernet(key)

TEMP_DIR = os.path.join(os.path.expanduser("~"), "Documents", "AirDropped Files")
os.makedirs(TEMP_DIR, exist_ok=True)

class FileSender(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        self.factory.app.status_text.insert(tk.END, "Connection made with receiver\n")
        if self.factory.app.selected_file:
            filename = os.path.basename(self.factory.app.selected_file)
            self.factory.app.status_text.insert(tk.END, f"Sending file: {filename}\n")
            self.transport.write(f"FILE {filename}\n".encode())
            with open(self.factory.app.selected_file, "rb") as f:
                file_data = f.read()
            encrypted_data = fernet.encrypt(file_data)
            self.transport.write(encrypted_data)
            self.transport.loseConnection()

class FileSenderFactory(protocol.Factory):
    def __init__(self, app):
        self.app = app

    def buildProtocol(self, addr):
        return FileSender(self)

class SignalingClientProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        self.factory.app.status_text.insert(tk.END, "Connected to signaling server\n")
        self.factory.signaling_connected = True

    def dataReceived(self, data):
        message = data.decode('utf-8')
        self.factory.app.status_text.insert(tk.END, f"Received message: {message}\n")
        if message.startswith("RECEIVER "):
            ip, port = message.split()[1].split(":")
            self.factory.receiver_ip = ip
            self.factory.receiver_port = int(port)
            self.factory.app.status_text.insert(tk.END, f"Receiver found at {ip}:{port}\n")
            self.factory.start_sending()

class SignalingClientFactory(protocol.Factory):
    def __init__(self, app):
        self.app = app
        self.signaling_connected = False
        self.receiver_ip = None
        self.receiver_port = None

    def buildProtocol(self, addr):
        return SignalingClientProtocol(self)

class SenderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AirDrop Sender")

        self.status_text = scrolledtext.ScrolledText(root, width=60, height=15, wrap=tk.WORD)
        self.status_text.pack(pady=20)

        self.file_button = tk.Button(root, text="Select File", command=self.select_file)
        self.file_button.pack(side=tk.LEFT, padx=10)

        self.send_button = tk.Button(root, text="Send File", command=self.send_file, state=tk.DISABLED)
        self.send_button.pack(side=tk.LEFT, padx=10)

        self.selected_file = None

        # Zeroconf for local discovery
        self.zeroconf = Zeroconf()
        self.browser = ServiceBrowser(self.zeroconf, "_airdrop._tcp.local.", handlers=[self.on_service_state_change])

        # Signaling server connection
        self.signaling_client = SignalingClientFactory(self)
        endpoint = endpoints.TCP4ClientEndpoint(reactor, "127.0.0.1", 6000)
        endpoint.connect(self.signaling_client).addErrback(self.handle_error)

    def on_service_state_change(self, zeroconf, service_type, name, state_change):
        if state_change is ServiceStateChange.Added:
            info = zeroconf.get_service_info(service_type, name)
            if info:
                ip = socket.inet_ntoa(info.addresses[0])  # Use the first address in the list
                port = info.port
                self.status_text.insert(tk.END, f"Local receiver found at {ip}:{port}\n")
                self.signaling_client.receiver_ip = ip
                self.signaling_client.receiver_port = port
                self.send_button.config(state=tk.NORMAL)

    def select_file(self):
        self.selected_file = filedialog.askopenfilename(initialdir=os.path.expanduser("~"), title="Select a File")
        if self.selected_file:
            self.status_text.insert(tk.END, f"Selected file: {self.selected_file}\n")
            self.send_button.config(state=tk.NORMAL)
        else:
            self.status_text.insert(tk.END, "No file selected.\n")

    def send_file(self):
        if not self.selected_file:
            self.status_text.insert(tk.END, "No file selected. Please select a file first.\n")
            return

        if self.signaling_client.receiver_ip is None or self.signaling_client.receiver_port is None:
            self.status_text.insert(tk.END, "No receiver found. Please wait for a receiver to connect.\n")
            return

        reactor.callFromThread(self.start_sending)

    def start_sending(self):
        endpoint = endpoints.TCP4ClientEndpoint(reactor, self.signaling_client.receiver_ip, self.signaling_client.receiver_port)
        endpoint.connect(FileSenderFactory(self)).addErrback(self.handle_error)

    def handle_error(self, error):
        self.status_text.insert(tk.END, f"Connection error: {error}\n")

    def __del__(self):
        self.zeroconf.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = SenderApp(root)

    def start_reactor():
        reactor.run(installSignalHandlers=False)

    reactor_thread = threading.Thread(target=start_reactor)
    reactor_thread.start()

    root.mainloop()
