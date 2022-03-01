import socket
import pickle
import time
import threading
from dataclasses import dataclass, field

empty = "—"
COST = {"torpedo": 900, "bomb": 600}

HEADERSIZE = 10

IP = "192.168.1.12"
PORT = 1234

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind((IP, PORT))
server_socket.listen(2)

clients = []
START_MONEY = 300

# Classes


@dataclass
class Client:
    """ Client class """
    money: int
    guess_board: list
    board: list
    ships: list
    client_socket: socket.socket = None


@dataclass
class Ship:
    """ Client ship class """
    name: str
    length: int
    sunk: False
    coords: list[tuple] = field(default_factory=list)


client1ships = [
    Ship(name="Aircraft Carrier", length=5, sunk=False),
    Ship(name="Battleship", length=4, sunk=False),
    Ship(name="Submarine", length=3, sunk=False),
    Ship(name="Cruiser", length=3, sunk=False),
    Ship(name="Destroyer", length=2, sunk=False)
]

client2ships = [
    Ship(name="Aircraft Carrier", length=5, sunk=False),
    Ship(name="Battleship", length=4, sunk=False),
    Ship(name="Submarine", length=3, sunk=False),
    Ship(name="Cruiser", length=3, sunk=False),
    Ship(name="Destroyer", length=2, sunk=False)
]

client1 = Client(money=START_MONEY, guess_board=[[empty for _ in range(10)] for _ in range(10)],
                 board=[[empty for _ in range(10)] for _ in range(10)], ships=client1ships)

client2 = Client(money=START_MONEY, guess_board=[[empty for _ in range(10)] for _ in range(10)],
                 board=[[empty for _ in range(10)] for _ in range(10)], ships=client2ships)


class Powerup:
    def __init__(self, powerup, client_class, opponent, client_move):
        self.powerup = powerup
        self.client_class = client_class
        self.opponent = opponent
        self.client_move = client_move
        self.client_ships = client_class.ships

    def use_powerup(self):
        if self.powerup == "torpedo" and self.client_class.money >= COST.get(self.powerup):
            self.torpedo()

        elif self.powerup == "bomb" and self.client_class.money >= COST.get(self.powerup):
            self.bomb()

    def torpedo(self):
        self.client_class.money -= COST.get(self.powerup)

        for y in range(len(self.opponent.board)):
            # If it is a hit

            condition1 = self.opponent.board[y][self.client_move[0]] == "x"
            condition2 = self.client_class.guess_board[y][self.client_move[0]] == empty

            if condition1 and condition2:
                self.client_class.guess_board, self.client_ships, self.client_class.money = \
                    make_hit(self.client_class, (self.client_move[0], y))
                break

            # Else, mark as a miss
            elif not condition1 and condition2:
                self.client_class.guess_board[y][self.client_move[0]] = "o"

        return self.client_ships, self.client_class.guess_board, self.client_class.money

    def bomb(self):
        self.client_class.money -= COST.get(self.powerup)

        # Iterate through the y direction
        for y in range(self.client_move[1] - 1, self.client_move[1] + 2):
            if y >= len(self.client_class.guess_board) or y < 0:
                continue

            condition1 = self.opponent.board[y][self.client_move[0]] == "x"
            condition2 = self.client_class.guess_board[y][self.client_move[0]]

            # If it is a hit
            if condition1 and condition2:
                self.client_class.guess_board, self.client_ships, self.client_class.money = \
                    make_hit(self.client_class, (self.client_move[0], y))

            elif not condition1 and condition2:
                self.client_class.guess_board[y][self.client_move[0]] = "o"

        # Iterate through the x direction
        for x in range(self.client_move[0] - 1, self.client_move[0] + 2):
            if x >= len(self.client_class.guess_board) or x < 0:
                continue

            condition1 = self.opponent.board[self.client_move[1]][x] == "x"
            condition2 = self.client_class.guess_board[self.client_move[1]][x] == empty

            # If it is a hit

            if condition1 and condition2:
                self.client_class.guess_board, self.client_ships, self.client_class.money = \
                    make_hit(self.client_class, (x, self.client_move[1]))

            elif not condition1 and condition2:
                self.client_class.guess_board[self.client_move[1]][x] = "o"

        return self.client_ships, self.client_class.guess_board, self.client_class.money


# Functions


def recieve(client_socket, pickled):  # Recieve a message
    message_header = client_socket.recv(HEADERSIZE)
    message_length = int(message_header.decode('utf-8').strip())

    if pickled:  # If the message was pickled
        message = client_socket.recv(message_length)
        return pickle.loads(message)

    return client_socket.recv(message_length).decode("utf-8")


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


def turns(client_class, opponent):  # Manages the turn of the current player
    send(client_class.client_socket, opponent.guess_board, True)  # Notify the client it is their turn
    powerup = recieve(pickled=False, client_socket=client_class.client_socket)  # Recieve the client's powerup
    move = recieve(pickled=True, client_socket=client_class.client_socket)  # Recieve the client's move

    print(f"Recieved move {move}")

    # Update the board
    hit = check_hit(*move, opponent.board)
    if powerup == "":
        client_class.guess_board[move[1]][move[0]] = "x" if hit == "hit" else "o"
        remove_ship(client_class.ships, move)

    else:
        Powerup(powerup, client_class, opponent, move).use_powerup()

    # Check if player sunk a ship
    sunk, client_class.ships = if_sank(client_class.ships)
    send(client_class.client_socket, sunk, True)

    send(client_class.client_socket, hit, False)  # Send the result of the guess back

    # Manage money and send it to the client
    client_class.money = manage_money(money=client_class.money, hit=hit, sunk=sunk)  # Manage money
    send(client_class.client_socket, client_class.money, True)  # Return money to client

    # Return if client won
    won = win_check(opponent.board, client_class.guess_board)

    # Send to all clients if the client won
    for client_socket in clients:
        send(client_socket, won, True)

    # Send guess board to client if the client didn't win
    if not won:
        send(client_socket=client_class.client_socket, message=client_class.guess_board, pickled=True)

    return client_class.guess_board, client_class.ships, client_class.money


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


def make_hit(client_class, client_move):
    client_class.guess_board[client_move[1]][client_move[0]] = "x"
    client_class.ships = remove_ship(client_class.ships, (client_move[0], client_move[1]))
    client_class.money += 150
    return client_class.guess_board, client_class.ships, client_class.money


def manage_money(money, hit, sunk):
    if hit == "hit":
        money += 150
    if sunk:
        money += 250
    return money + 75


def if_won(client_list):
    # Send clients each other's boards
    send(client1.client_socket, client2.board, True)
    send(client2.client_socket, client1.board, True)

    # Reset client classes
    client_class1 = Client(money=START_MONEY, guess_board=[[empty for _ in range(10)] for _ in range(10)],
                           board=[[empty for _ in range(10)] for _ in range(10)], ships=[])

    client_class2 = Client(money=START_MONEY, guess_board=[[empty for _ in range(10)] for _ in range(10)],
                           board=[[empty for _ in range(10)] for _ in range(10)], ships=[])

    # Recieve if the clients want to playagain
    client1_playagain = recieve(client1.client_socket, False).lower()
    client2_playagain = recieve(client2.client_socket, False).lower()

    # Handle clients disconnecting
    if client1_playagain == "n":
        print("Client 1 disconnected.")
        client_list.remove(client_list[0])

    if client2_playagain == "n":
        print("Client 2 diconnected.")
        client_list.remove(client_list[1])

    return client_list, client_class1, client_class2


if __name__ == "__main__":
    while True:
        t = threading.Thread(target=manage_clients)
        t.start()

        # Wait for players to connect

        print("Waiting for players to connect.")
        while len(clients) < 2:
            time.sleep(1)

        while len(clients) >= 2:
            client1.client_socket = clients[0]
            client2.client_socket = clients[1]
            # Notify clients to start the game
            print("Starting game")
            for client in clients:
                send(client_socket=client, message="game start", pickled=True)

            # Send prices
            for client in clients:
                send(client_socket=client, pickled=True, message=COST)

            # Send money
            send(clients[0], client1.money, True)
            send(clients[1], client2.money, True)

            # Recieve the player's battleship placements

            client1.client_socket = clients[0]
            client2.client_socket = clients[1]

            client1.board = recieve(client1.client_socket, True)
            client2.board = recieve(client2.client_socket, True)
            client1_ship_list = recieve(client1.client_socket, True)
            client2_ship_list = recieve(client2.client_socket, True)

            # Input ship coordinates for client 1
            for coordinates in client1_ship_list:
                for ship in client1.ships:
                    if len(coordinates) == ship.length and not ship.coords:
                        ship.coords = coordinates
                        break

            # Input ship coordiantes for client 2
            for coordinates in client2_ship_list:
                for ship in client2.ships:
                    if len(coordinates) == ship.length and not ship.coords:
                        ship.coords = coordinates
                        break

            # Send to client 1 if they won (the client is expecting this information)
            send(client1.client_socket, win_check(client1.board, client1.guess_board), True)

            # Main game loop
            turn = "client1"
            while True:
                # Handle client 1's turn
                if turn == "client1":
                    turn = "client2"
                    client1.guess_board, client1.ships, client1.money = turns(client1, client2)

                    # If the client won, reset game
                    if win_check(client2.board, client1.guess_board):
                        clients, client1, client2 = if_won(clients)
                        break

                elif turn == "client2":
                    # Handle client 2's turn
                    turn = "client1"
                    client2.guess_board, client2.ships, client2.money = turns(client2, client1)

                    # If the client won, reset game
                    if win_check(client1.board, client2.guess_board):
                        clients, client1, client2 = if_won(clients)
                        break
