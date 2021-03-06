import socket
import pickle
import copy
import colorama
from colorama import Fore, Back
from dataclasses import dataclass

# Initiate coloroma

colorama.init(autoreset=True)

# Define vars

HEADERSIZE = 10
user = ""
move_x, move_y = 0, 0

EMPTY = "—"

# Connect to server

IP = input("IP: ")
PORT = int(input("Port: "))

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((IP, PORT))

# Classes


class Statistics:
    """ Stats class"""
    def __init__(self):
        self.wins = 0
        self.losses = 0
        self.moves = 0
        self.hits = 0

    def reset(self):
        self.moves = 0
        self.hits = 0


@dataclass
class Client:
    """ Client class """
    money: int
    guess_board: list
    board: list
    stats: Statistics


class Shop:
    def __init__(self, balance, prices):
        self.balance = balance
        self.prices = prices
        self.client_powerup = ""

    def run_shop(self):
        self.print_shop()
        self.get_user_powerup()
        while True:
            client_move, self.client_powerup, coord_error = self.get_powerup_coords()
            if coord_error is False:
                break

        return client_move, self.client_powerup

    def print_shop(self):
        # Print the items available in the shop
        print(f"——— SHOP ———\n"
              f"Your money: ${self.balance}\n\n")

        for item in self.prices:
            print(f"{item.capitalize()}: ${self.prices.get(item)[0]}:    {self.prices.get(item)[1]}")

    def get_user_powerup(self):
        while True:
            try:
                self.client_powerup = input("Your powerup or type \"exit\" to exit: ")
                self.client_powerup = self.client_powerup.lower()

                # If the client exited
                if self.client_powerup == "exit":
                    self.client_powerup = ""
                    break

                # Check if the client has enough money to buy the powerup
                elif self.prices.get(self.client_powerup)[0] <= self.balance:
                    print(f"{Fore.GREEN}Successfully bought {self.client_powerup}.")

                else:
                    print(f"{Fore.RED}You do not have enough money to buy that!\n")
                    continue
                break

            except TypeError:
                print(f"{Fore.RED}Please input a valid powerup. Type \"exit\" to exit.")

    def get_powerup_coords(self):
        try:
            if self.client_powerup == "torpedo":
                client_move = int(input("Input the x coordinate of your powerup: "))
                client_move = f"{client_move}, 1"

            elif self.client_powerup == "bomb":
                client_move = input("Input coordiantes of your powerup: ")

            elif self.client_powerup == "recon plane":
                client_move = "1, 1"

            else:
                return None, "", False

            # Split client_move into 2 vars
            client_move = client_move.split(",")
            client_move_x = int(client_move[0].replace(" ", "")) - 1
            client_move_y = int(client_move[1].replace(" ", "")) - 1

            if client_move_x >= 10 and client_move_y >= 10:
                print(f"{Fore.RED}Please input valid coordinates!")
                return client_move, self.client_powerup, True
            return [client_move_x, client_move_y], self.client_powerup, False

        except (ValueError, TypeError):
            print(f"{Fore.RED}Please input valid coordinates!")
            return None, "", True


# Functions


def send(socket_client, message, pickled):
    message = pickle.dumps(message) if pickled else message.encode("utf-8")
    message = f"{len(message):<{HEADERSIZE}}".encode("utf-8") + message
    socket_client.send(message)


def merge_board(ship_board, player_guess_board):
    output_board = [[EMPTY for _ in range(10)] for _ in range(10)]
    for f in range(len(ship_board)):
        for x in range(len(ship_board)):
            # If guess_board has a hit, make it a capital X
            if ship_board[f][x] == "x":
                if player_guess_board[f][x] == "x":
                    output_board[f][x] = "X"
                else:
                    output_board[f][x] = ship_board[f][x]
            else:
                output_board[f][x] = player_guess_board[f][x]

    return output_board


def print_board(current_board):  # Prints the board.
    # Print numbers on the x axis
    print("0  ", end="")
    for x in range(len(current_board)):
        print(x + 1, end="  ")
    print("\n"*0)

    for f in range(len(current_board)):
        # Print numbers on the y axis
        end = "  " if f < 9 else " "
        print(str(f + 1), end=end)

        # Print board content
        for x in range(len(current_board)):
            if str(current_board[f][x]) == "x":
                color = Fore.RED

            elif str(current_board[f][x]) == "X":
                color = Back.RED

            elif str(current_board[f][x]) == EMPTY:
                color = Fore.BLUE

            else:
                color = ""

            print(f"{color}{current_board[f][x]}", end="  ")
        print()


def recieve(pickled):  # Recieve a message
    message_header = client_socket.recv(HEADERSIZE)
    message_length = int(message_header.decode('utf-8').strip())

    if pickled:  # If the message was pickled
        message = client_socket.recv(message_length)
        return pickle.loads(message)

    return client_socket.recv(message_length).decode("utf-8")


def if_won(user_won):
    global client, user
    opponent_board = recieve(pickled=True)
    print("\nEnemy's board:")
    print_board(opponent_board)

    if user_won:
        print("You win!\n"*3)
        client.stats.wins += 1
    else:
        print("You lose.\n"*3)
        client.stats.losses += 1

    # Reset variables
    client.board = [[EMPTY for _ in range(10)] for _ in range(10)]
    client.guess_board = [[EMPTY for _ in range(10)] for _ in range(10)]

    # Show stats
    print(f"Wins: {client.stats.wins} Losses: {client.stats.losses}")
    if client.stats.losses > 0:
        print(f"Win/Loss Ratio: {round(client.stats.wins / client.stats.losses, 2)}")
    print(f"Moves: {client.stats.moves} Hits: {client.stats.hits}")
    if client.stats.hits > 0:
        print(f"Miss/Hit Ratio: {round((client.stats.moves-client.stats.hits) / client.stats.hits, 2)}")
    client.stats.reset()

    user = input("Do you want to play again? (y/n) ")
    send(client_socket, user, False)  # Send if the client is playing again to the server
    return user


stats = Statistics()
client = Client(0, [[EMPTY for _ in range(10)] for _ in range(10)], [[EMPTY for _ in range(10)] for _ in range(10)],
                stats)

while True:
    if user == "n":  # If the user exited the script, break from all loops
        break

    print("Waiting for game to start...")

    try:
        start = recieve(pickled=True)  # Recieve the game start message

        POWERUPS = dict(recieve(pickled=True))  # Prices of powerups
        client.money = recieve(pickled=True)  # Recieve money

        if start != "game start":
            print("An unexpected error occured.")
            break

        # Let the user place ships
        ship_lens = [5, 4, 3, 3, 2]
        ship_coords = []
        temp_coords = []
        temp_board = copy.deepcopy(client.board)
        error = False

        for ship_len in ship_lens:
            while True:
                try:
                    print_board(client.board)
                    print(f"Ship length: {ship_len}")
                    direction = input("Enter ship direction (up, down, left, right): ")
                    move = input("Enter a ship placement (x, y): ")
                    move = move.split(",")

                    move_x = int(move[0].replace(" ", "")) - 1
                    move_y = int(move[1].replace(" ", "")) - 1

                    # Check if number is < 0
                    if move_x < 0 or move_y < 0:
                        print(f"{Fore.RED}Please input a number greater than 0.")
                        continue

                    error = False
                    temp_board = copy.deepcopy(client.board)
                    temp_coords = []

                    # If the boat direciton is horizontal
                    if direction == "right" or direction == "r":
                        for i in range(ship_len):
                            if client.board[move_y][move_x + i] == "x":
                                print(Fore.RED + "Ship intersects another ship.")
                                error = True
                                break
                            temp_board[move_y][move_x + i] = "x"
                            temp_coords.append((move_x + i, move_y))

                    # If the boat direction is vertical
                    elif direction == "down" or direction == "d":
                        for i in range(ship_len):
                            if client.board[move_y + i][move_x] == "x":
                                print(Fore.RED + "Ship intersects another ship.")
                                error = True
                                break
                            temp_board[move_y + i][move_x] = "x"
                            temp_coords.append((move_x, move_y + i))

                    elif direction == "left" or direction == "l":
                        for i in range(ship_len):
                            if client.board[move_y][move_x - i] == "x":
                                print(Fore.RED + "Ship intersects another ship.")
                                error = True
                                break
                            temp_board[move_y][move_x - i] = "x"
                            temp_coords.append((move_x - i, move_y))

                    elif direction == "up" or direction == "u":
                        for i in range(ship_len):
                            if client.board[move_y - i][move_x] == "x":
                                print(Fore.RED + "Ship intersects another ship.")
                                error = True
                                break
                            temp_board[move_y - i][move_x] = "x"
                            temp_coords.append((move_x, move_y - i))

                    else:
                        print(f"{Fore.RED}Input a ship direction of \"up\", \"down\", \"left\", or \"right\".")
                        continue

                    # If there was an error
                    if error:
                        continue

                    client.board = temp_board
                    ship_coords.append(temp_coords)

                    break

                except ValueError:
                    print(f"{Fore.RED}Input valid formatting: \"x, y\"")

                except IndexError:
                    print(f"{Fore.RED}Ship exited the board. Please try a different placement.")

        # Send board
        send(client_socket, client.board, True)

        # Send ship locations
        send(client_socket, ship_coords, True)
        print_board(client.board)

        print("Waiting for enemy...\n")

        # Main game loop
        while True:
            won = recieve(pickled=True)
            if won is True:
                user = if_won(False)
                break

            opponent_guess_board = recieve(pickled=True)
            client.stats.moves += 1

            powerup = ""
            while True:
                try:
                    # Print the player's guesses and ask for a guess
                    merged_board = merge_board(ship_board=client.board, player_guess_board=opponent_guess_board)
                    print("\nEnemy's guess board:")
                    print_board(merged_board)
                    print(f"\nYour guess board:")
                    print_board(client.guess_board)

                    print(Fore.GREEN + f"Money: ${client.money}")
                    move = input("\nEnter a guess (x, y) or type \"shop\" for more options: ")

                    # Shop
                    if move.lower() == "shop":
                        s = Shop(client.money, POWERUPS)
                        move, powerup = s.run_shop()

                    if not move:
                        continue

                    if powerup == "":
                        move = move.split(",")
                        move_x = int(move[0].replace(" ", "")) - 1
                        move_y = int(move[1].replace(" ", "")) - 1

                        if client.guess_board[move_y][move_x] != EMPTY:
                            print(f"{Fore.RED}You already guessed that spot!")
                            continue
                    else:
                        move_x = move[0]
                        move_y = move[1]
                    break

                except (ValueError, IndexError):
                    print(f"{Fore.RED}Please input valid formatting: \"x, y\"")
                    continue

            # Send the powerup and move to the server
            send(client_socket, powerup, False)
            send(client_socket, (move_x, move_y), True)

            # Recieve if a ship was sunk
            sunk = recieve(pickled=True)

            # Recieve the result of the move
            result = recieve(pickled=False)
            if result == "hit":
                print(f"{Fore.GREEN}Hit!")
                client.stats.hits += 1

            if sunk:
                print(f"{Fore.GREEN}You sunk your enemy's {sunk}!\n"*2)

            # Recieve money
            client.money = recieve(pickled=True)

            # Recieve if you won
            won = recieve(pickled=True)
            if won is True:
                user = if_won(True)
                break

            # Recieve guess board
            client.guess_board = recieve(pickled=True)
            print_board(client.guess_board)

            # Wait for the enemy to execute their turn
            print("Waiting for enemy...")

    except ConnectionResetError:
        print("An existing connection was forcibly closed by the remote host")
        break
