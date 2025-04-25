"""
Summary: Reciever to pair wih the sender.

Instructions:
Replace "your key" below with the same key used in your sender. Share the updated "sender_base.py" and "server_base.py" to people you want to allow to send/recieve files from.

"""
import os
import threading
import socket
from cryptography.fernet import Fernet
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from twisted.internet import reactor, protocol, endpoints
from zeroconf import ServiceInfo, Zeroconf

# Hard-coded Fernet key
key = your key # Replace with your generated key
fernet = Fernet(key)

TEMP_DIR = os.path.join(os.path.expanduser("~"), "Documents", "AirDropped Files")
os.makedirs(TEMP_DIR, exist_ok=True)

class FileReceiver(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.receiving_file = False
        self.filename = ""
        self.file_data = b""

    def dataReceived(self, data):
        if not self.receiving_file:
            if data.startswith(b"FILE "):
                self.filename = data[5:].decode().strip()
                self.factory.app.status_text.insert(tk.END, f"Receiving file: {self.filename}\n")
                self.receiving_file = True
        else:
            self.file_data += data
            # Assuming the file is sent in one chunk
            if len(self.file_data) > 0:
                self.process_received_file()
                self.receiving_file = False
                self.filename = ""
                self.file_data = b""

    def process_received_file(self):
        try:
            decrypted_data = fernet.decrypt(self.file_data)
            file_path = os.path.join(TEMP_DIR, self.filename)
            with open(file_path, "wb") as f:
                f.write(decrypted_data)
            self.factory.app.status_text.insert(tk.END, f"Received and decrypted file: {self.filename}\n")
            copy_yn = messagebox.askyesno("Copy File", "Copy file to another folder?")
            if copy_yn:
                new_dir = filedialog.askdirectory(initialdir=os.path.join(os.path.expanduser("~"), "Documents"))
                if new_dir:
                    saveto = os.path.join(new_dir, self.filename)
                    with open(saveto, "wb") as f:
                        f.write(decrypted_data)
                    self.factory.app.status_text.insert(tk.END, "Copied!\n")
            else:
                self.factory.app.status_text.insert(tk.END, "File saved in AirDropped Files folder.\n")
        except Exception as e:
            self.factory.app.status_text.insert(tk.END, f"Decryption error: {e}\n")

class FileReceiverFactory(protocol.Factory):
    def __init__(self, app):
        self.app = app

    def buildProtocol(self, addr):
        return FileReceiver(self)

class SignalingClientProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        self.factory.app.status_text.insert(tk.END, "Connected to signaling server\n")
        self.factory.signaling_connected = True
        self.transport.write(f"RECEIVER {self.factory.ip}:{self.factory.port}\n".encode())

class SignalingClientFactory(protocol.Factory):
    def __init__(self, app, ip, port):
        self.app = app
        self.signaling_connected = False
        self.ip = ip
        self.port = port

    def buildProtocol(self, addr):
        return SignalingClientProtocol(self)

class ReceiverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AirDrop Receiver")

        self.status_text = scrolledtext.ScrolledText(root, width=60, height=15, wrap=tk.WORD)
        self.status_text.pack(pady=20)

        # Zeroconf for advertising
        self.zeroconf = Zeroconf()
        ip_address = socket.gethostbyname(socket.gethostname())
        self.info = ServiceInfo(
            "_airdrop._tcp.local.",
            "AirDropReceiver._airdrop._tcp.local.",
            addresses=[socket.inet_aton(ip_address)],
            port=6001,
            properties={},
            server=f"{socket.gethostname()}.local."
        )
        self.zeroconf.register_service(self.info)

        # Signaling server connection
        self.ip = ip_address
        self.port = 6001
        self.signaling_client = SignalingClientFactory(self, self.ip, self.port)
        endpoint = endpoints.TCP4ClientEndpoint(reactor, "127.0.0.1", 0)  # Use port 0 to let the system choose an available port
        d = endpoint.connect(self.signaling_client)
        d.addCallback(self.handle_signaling_connection)
        d.addErrback(self.handle_error)

        # Twisted server for receiving files
        endpoint = endpoints.TCP4ServerEndpoint(reactor, 6001)
        endpoint.listen(FileReceiverFactory(self))
        self.status_text.insert(tk.END, f"Listening on {self.ip}:{self.port}\n")

    def handle_signaling_connection(self, protocol):
        self.status_text.insert(tk.END, "Connected to signaling server\n")

    def handle_error(self, error):
        self.status_text.insert(tk.END, f"Connection error: {error}\n")

    def __del__(self):
        self.zeroconf.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = ReceiverApp(root)

    def start_reactor():
        reactor.run(installSignalHandlers=False)

    reactor_thread = threading.Thread(target=start_reactor)
    reactor_thread.start()

    root.mainloop()
