# AirDrop

Summary: A simple file transfer app for sending/receiving files securely over a server.

# How to Use
1. Run "keygen.py" and copy the output you got (i.e. b'gAAAAAAgtw2i3'), including the b.
2. Paste this into server_base.py and sender_base.py where it says to replace with your key.
3. Once you have done this, you can send the updated version of server_base.py and sender_base.py to people you want to be able to receive files from/send files to.
4. Start by running "server_base.py" to open the server on your end.
5. You can have another person run "sender_base.py" to send a file to you.
6. Since V2.0.0, users on different networks can now send files to each other as long as signaling.py is running (REQUIRED)
7. When you receive a file, it will download it into a folder named "AirDropped Files" in your Documents folder. Don't worry, if you don't make the folder yourself, the program makes it for you.
# How it Works
1. The server opens on port 6000. It starts listening on all interfaces for a signal from the sender.
2. When a file is sent, it is read as binary data and encrypted. This encrypted data is then sent to the server.
3. When the server receives a response, it decodes it and saves it for you.
