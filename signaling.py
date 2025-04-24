import tkinter as tk
from tkinter import scrolledtext
from twisted.internet import reactor, protocol, endpoints
import threading

class SignalingProtocol(protocol.Protocol):
    def connectionMade(self):
        self.factory.clients.append(self)
        self.factory.app.status_text.insert(tk.END, "New client connected\n")

    def dataReceived(self, data):
        message = data.decode('utf-8')
        self.factory.app.status_text.insert(tk.END, f"Received message: {message}\n")
        for client in self.factory.clients:
            if client != self:
                client.transport.write(data)

    def connectionLost(self, reason):
        self.factory.clients.remove(self)
        self.factory.app.status_text.insert(tk.END, "Client disconnected\n")

class SignalingFactory(protocol.Factory):
    def __init__(self, app):
        self.app = app
        self.clients = []

    def buildProtocol(self, addr):
        return SignalingProtocol(self)

class SignalingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Signaling Server")

        self.status_text = scrolledtext.ScrolledText(root, width=60, height=15, wrap=tk.WORD)
        self.status_text.pack(pady=20)

        endpoint = endpoints.TCP4ServerEndpoint(reactor, 6000)
        endpoint.listen(SignalingFactory(self))
        self.status_text.insert(tk.END, "Listening on 127.0.0.1:6000\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = SignalingApp(root)

    def start_reactor():
        reactor.run(installSignalHandlers=False)

    reactor_thread = threading.Thread(target=start_reactor)
    reactor_thread.start()

    root.mainloop()