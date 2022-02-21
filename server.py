import socket
import pickle
import time
import threading
from dataclasses import dataclass, field

empty = "—"
cost = {"torpedo": 900, "bomb": 600}

HEADERSIZE = 10

IP = "192.168.1.12"
PORT = 1234

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind((IP, PORT))
server_socket.listen(2)

clients = []

turn = "client1"

# Classes


@dataclass
class Client:
    """ Client 1 class """
    money: int
    guess_board: list
    board: list


client1 = Client(money=350, guess_board=[[empty for _ in range(10)] for _ in range(10)], board=[])
client2 = Client(money=350, guess_board=[[empty for _ in range(10)] for _ in range(10)], board=[])


@dataclass
class Client1Ship:
    """ Client 1 ship class """
    name: str
    length: int
    sunk: False
    coords: list[tuple] = field(default_factory=list)


client1ships = [
    Client1Ship(name="Aircraft Carrier", length=5, sunk=False),
    Client1Ship(name="Battleship", length=4, sunk=False),
    Client1Ship(name="Submarine", length=3, sunk=False),
    Client1Ship(name="Cruiser", length=3, sunk=False),
    Client1Ship(name="Destroyer", length=2, sunk=False)
]


@dataclass
class Client2Ship:
    """ Client 1 ship class """
    name: str
    length: int
    sunk: False
    coords: list[tuple] = field(default_factory=list)


client2ships = [
    Client2Ship(name="Aircraft Carrier", length=5, sunk=False),
    Client2Ship(name="Battleship", length=4, sunk=False),
    Client2Ship(name="Submarine", length=3, sunk=False),
    Client2Ship(name="Cruiser", length=3, sunk=False),
    Client2Ship(name="Destroyer", length=2, sunk=False)
]


def recieve(client_socket, pickled):  # Recieve a message
    try:
        message_header = client_socket.recv(HEADERSIZE)
        message_length = int(message_header.decode('utf-8').strip())

        if pickled:  # If the message was pickled
            message = client_socket.recv(message_length)
            message = pickle.loads(message)

        else:
            message = client_socket.recv(message_length).decode("utf-8")

        return message
    except ConnectionResetError:
        clients.remove(client_socket)
        print("Client disconnected.")


def send(client_socket, message, pickled):
    message = pickle.dumps(message) if pickled else message.encode("utf-8")
    message = f"{len(message):<{HEADERSIZE}}".encode("utf-8") + message

    try:
        client_socket.send(message)

    except ConnectionResetError:
        clients.remove(client_socket)
        print("Client disconnected.")


def manage_clients():  # Handle clients connecting and disconnecting
    while True:
        clientsocket, address = server_socket.accept()

        # Accepts only 2 clients
        if len(clients) > 1:
            print(f"{address} tried to connect but the socket was closed by the server.")
            clientsocket.close()

        else:
            clients.append(clientsocket)
            print(f"{address} connected. {len(clients)}/2 connected.")


def check_hit(x, y, current_board):  # Check if the cilent hit or miss.
    return "hit" if current_board[y][x] == "x" else "miss"


def win_check(current_board, guess_board):  # Check if the client won
    for i in range(len(current_board)):
        for x in range(len(current_board)):
            if guess_board[i][x] == empty and current_board[i][x] == "x":
                return False
    return True


def turns(client_socket, client_guess_board, opponent_board, opponent_guess_board,
          opponent_client_socket, client_board, client_ships, money):
    # Notify the client it is their turn
    send(client_socket, opponent_guess_board, True)

    # Recieve the client's powerup
    powerup = recieve(pickled=True, client_socket=client_socket)

    # Recieve the client's move
    move = recieve(pickled=True, client_socket=client_socket)

    client_move_x = move[0]
    client_move_y = move[1]

    # Update the board
    client_ships, client_guess_board, money = update_board(powerup, money, opponent_board, client_guess_board,
                                                                  (client_move_x, client_move_y), client_ships)
    # Check if player sunk a ship

    result, client_ships = if_sank(client_ships)
    send(client_socket, result, True)

    if result:
        money += 250

    # Check if the cient's move is a hit and send the result back
    hit = check_hit(client_move_x, client_move_y, opponent_board)

    send(client_socket, hit, False)
    if hit == "hit" and powerup == "":
        money += 150

    # Send money to client
    send(client_socket, money, True)

    # Return if client won
    win = win_check(opponent_board, client_guess_board)

    for clients_socket in clients:
        send(clients_socket, win, True)

    # Send guess board to client

    send(client_socket=client_socket, message=client_guess_board, pickled=True)

    # If the client won, send each other's ship placements
    if win_check(opponent_board, client_guess_board):
        # Send to client socket
        send(client_socket, opponent_board, True)

        # Send to opponent client socket
        send(opponent_client_socket, client_board, True)

    return client_guess_board, client_ships, money


def remove_ship(ships, coords):  # Removes ship from ship class
    for client_ship in ships:
        for coord in client_ship.coords:
            if coord == coords:
                client_ship.coords.remove(coords)
    return ships


def if_sank(ships):  # Checks if the user sank a ship
    for client_ship in ships:
        if len(client_ship.coords) == 0 and not client_ship.sunk:
            client_ship.sunk = True
            return client_ship.name, ships
    return False, ships


def update_board(powerup, money, opponent_board, client_guess_board, client_move, client_ships):
    # If no powerup is used
    if powerup == "":
        client_guess_board[client_move[1]][client_move[0]] = "x" if opponent_board[client_move[1]][client_move[0]] \
                                                                    == "x" else "o"
        return remove_ship(client_ships, client_move), client_guess_board, money

    # Use the powerup
    elif powerup.lower() == "torpedo" and money >= cost["torpedo"]:  # If the powerup is the torpedo
        money -= cost["torpedo"]

        for y in range(len(opponent_board)):
            # If it is a hit
            if opponent_board[y][client_move[0]] == "x" and client_guess_board[y][client_move[0]] == empty:
                client_guess_board[y][client_move[0]] = "x"
                remove_ship(client_ships, (client_move[0], y))
                money += 150
                break
            # Else, mark as a miss
            else:
                client_guess_board[y][client_move[0]] = "o"

    elif powerup.lower() == "bomb" and money >= cost["bomb"]:
        money -= cost["bomb"]
        print(money)
        # Iterate through the y direction
        for y in range(client_move[1] - 1, client_move[1] + 2):
            if opponent_board[y][client_move[0]] == "x":
                client_guess_board[y][client_move[0]] = "x"
                remove_ship(client_ships, (client_move[0], y))
                money += 150

            else:
                client_guess_board[y][client_move[0]] = "o"

        # Iterate through the x direction
        for x in range(client_move[0] - 1, client_move[0] + 2):
            if opponent_board[client_move[1]][x] == "x":
                client_guess_board[client_move[1]][x] = "x"
                remove_ship(client_ships, (x, client_move[1]))

            else:
                client_guess_board[client_move[1]][x] = "o"

    return client_ships, client_guess_board, money


if __name__ == "__main__":
    t = threading.Thread(target=manage_clients)
    t.start()

    # Wait for players to connect

    print("Waiting for players to connect.")
    while len(clients) < 2:
        time.sleep(1)

    while len(clients) >= 2:
        # Notify clients to start the game

        for client in clients:
            send(client_socket=client, message="game start", pickled=False)

        # Send prices
        for client in clients:
            send(client_socket=client, pickled=True, message=cost)

        # Send money
        send(clients[0], client1.money, True)
        send(clients[1], client2.money, True)

        # Recieve the player's battleship placements

        client1_socket = clients[0]
        client2_socket = clients[1]

        client1.board = recieve(client1_socket, True)
        client2.board = recieve(client2_socket, True)
        client1_ship_list = recieve(client1_socket, True)
        client2_ship_list = recieve(client2_socket, True)

        # Input ship coordinates for client 1
        for coordinates in client1_ship_list:
            for ship in client1ships:
                if len(coordinates) == ship.length and not ship.coords:
                    ship.coords = coordinates
                    break

        # Input ship coordiantes for client 2
        for coordinates in client2_ship_list:
            for ship in client2ships:
                if len(coordinates) == ship.length and not ship.coords:
                    ship.coords = coordinates
                    break

        # Send to client 1 if they won (the client is expecting this information)
        send(client1_socket, win_check(client1.board, client1.guess_board), True)

        # Main game loop
        while True:
            # Handle client 1's turn
            if turn == "client1":
                turn = "client2"
                client1.guess_board, client1ships, client1.money = turns(client1_socket, client1.guess_board,
                                                                         client2.board, client2.guess_board,
                                                                         client2_socket, client1.board,
                                                                         client1ships, client1.money)

                # If the client won, reset game
                if win_check(client2.board, client1.guess_board):
                    turn = "client1"
                    client1.guess_board = [[empty for _ in range(10)] for _ in range(10)]
                    client2.guess_board = [[empty for _ in range(10)] for _ in range(10)]
                    time.sleep(10)
                    break

            elif turn == "client2":
                # Handle client 2's turn
                turn = "client1"
                client2.guess_board, client2ships, client2.money = turns(client2_socket, client2.guess_board,
                                                                         client1.board, client1.guess_board,
                                                                         client1_socket, client2.board,
                                                                         client2ships, client2.money)

                # If the client won, reset game
                if win_check(client1.board, client2.guess_board):
                    client1.guess_board = [[empty for _ in range(10)] for _ in range(10)]
                    client2.guess_board = [[empty for _ in range(10)] for _ in range(10)]
                    time.sleep(10)
                    break
