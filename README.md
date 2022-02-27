# Battleship-Multiplayer

A multiplayer Battleship game in Python.

TO RUN A SERVER:
1. Download server.py and open it with an IDE. Under the IP constant, change it to your local ip. On windows, you can find this under the default gateway in ipconfig.
2. To have players connect from the internet, port forward whatever port the PORT constant is set to (default is 1234). If players are connecting from LAN, connect to the local IP set in the IP constant.
3. Run server.py.

TO CONNECT TO A SERVER:
1. Download client_exe zip file. Extract it and run client_console.exe.
2. If the host is port forwarding, connect to their public IP address. If you are connecting via LAN, input the host's local IP address.
3. Enter the port. This is the PORT constant in server.py (default is 1234).

TO PLAY THE GAME:
1. Place your ships. Horizontal ships start from the given coordinate and generate to the right. Vertical ships start from the given coordinate and generate downwards.
2. Play the start of the game as you would in the normal Battleship game.
3. After gaining enough money by hitting and sinking ships, buy something from the shop by typing "shop".
4. Input your desired powerup.
