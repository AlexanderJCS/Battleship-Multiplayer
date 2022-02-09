# Battleship-Multiplayer

A multiplayer Battleship game in Python.

TO RUN A SERVER:
1. Download server.py and open it with an IDE. Under the IP constant, change it to your local ip. On windows, you can find this under the default gateway in ipconfig.
2. To have players connect from the internet, port forward whatever port the PORT constant is set to (default is 1234). If players are connecting from LAN, connect to the local IP set in the IP constant.
3. Run server.py.

TO CONNECT TO A SERVER:
1. Download client.py (if you have Python) or client.exe (if you don't have Python) and run it.
2. If the host is port forwarding, connect to their public IP address. If you are connecting via LAN, input the host's local IP address.
3. Enter the port. This is the PORT constant in server.py (default is 1234).
4. Place your ships. Placing ships horizontally starts from the coordinate inputted and generates the ship to the right. Vertical starts at the given coordinate and generates the ship downward.
5. Guess each other's ship positions and have fun!
