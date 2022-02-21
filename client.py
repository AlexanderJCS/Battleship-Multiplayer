import socket
import pickle
import copy
import colorama
from colorama import Fore, Back

# Initiate coloroma

colorama.init(autoreset=True)

# Define vars

HEADERSIZE = 10
wins = 0
losses = 0
moves = 0
hits = 0
user = ""
move_x, move_y = 0, 0

empty = "—"
board = [[empty for _ in range(10)] for _ in range(10)]
guess_board = [[empty for _ in range(10)] for _ in range(10)]
error = False


# Functions


def merge_board(ship_board, player_guess_board):
    output_board = [[empty for _ in range(10)] for _ in range(10)]
    for f in range(len(ship_board)):
        for x in range(len(ship_board)):
            # If guess_board has a hit, make it a capital X
            if ship_board[f][x] == "x" and player_guess_board[f][x] == "x":
                output_board[f][x] = "X"

            elif ship_board[f][x] == "x":
                output_board[f][x] = "x"

            elif player_guess_board[f][x] == "o":
                output_board[f][x] = "o"
    return output_board


def print_board(current_board):  # Prints the board.
    # Print numbers on the x axis
    print("0  ", end="")
    for x in range(len(board)):
        print(x + 1, end="  ")
    print("\n"*0)

    for f in range(len(board)):
        # Print numbers on the y axis
        end = "  " if f < 9 else " "
        print(str(f + 1), end=end)

        # Print board content
        for x in range(len(board)):
            if str(current_board[f][x]) == "x":
                print(Fore.RED + str(current_board[f][x]), end="  ")

            elif str(current_board[f][x]) == "X":
                print(Back.RED + str(current_board[f][x]), end="  ")

            elif str(current_board[f][x]) == empty:
                print(Fore.BLUE + str(current_board[f][x]), end="  ")

            else:
                print(str(current_board[f][x]), end="  ")

        print("\n"*0)


def recieve(pickled):  # Recieve a message
    message_header = client_socket.recv(HEADERSIZE)
    message_length = int(message_header.decode('utf-8').strip())

    if pickled:  # If the message was pickled
        message = client_socket.recv(message_length)
        return pickle.loads(message)

    return client_socket.recv(message_length).decode("utf-8")


def if_won(user_won):
    global opponent_board, board, guess_board, losses, hits, moves, user, wins
    opponent_board = recieve(pickled=True)
    print("\nEnemy's board:")
    print_board(opponent_board)

    if user_won:
        print("You win!\n"*3)
        wins += 1
    else:
        print("You lose.\n"*3)
        losses += 1

    # Reset variables
    board = [[empty for _ in range(10)] for _ in range(10)]
    guess_board = [[empty for _ in range(10)] for _ in range(10)]

    # Show stats
    print(f"Wins: {wins} Losses: {losses}")
    if losses > 0:
        print(f"Win/Loss Ratio: {round(wins / losses, 2)}")
    print(f"Moves: {moves} Hits: {hits}")
    if hits > 0:
        print(f"Miss/Hit Ratio: {round((moves-hits) / hits, 2)}")
    moves = 0
    hits = 0

    user = input("Do you want to exit? (y/n) ")


while True:
    try:
        # Connect to server

        IP = input("IP: ")
        PORT = int(input("Port: "))

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((IP, PORT))

        print("Waiting for game to start...")

        if user == "y":  # If the user exited the script, break from all loops
            break

        start = recieve(pickled=False)  # Recieve the game start message
        cost = dict(recieve(pickled=True))  # Prices of powerups
        money = recieve(pickled=True)

        if start != "game start":
            print("An unexpected error occured.")
            break

        # Let the user place ships
        ship_lens = [5, 4, 3, 3, 2]
        ship_coords = []
        temp_coords = []
        temp_board = copy.deepcopy(board)
        for ship_len in ship_lens:
            while True:
                try:
                    print_board(board)
                    print(f"Ship length: {ship_len}")
                    direction = input("Enter ship direction (horizontal, vertical): ")
                    move = input("Enter a ship placement (x, y): ")
                    move = move.split(",")
                    move_x = int(move[0].replace(" ", "")) - 1
                    move_y = int(move[1].replace(" ", "")) - 1

                    # Some error checks
                    if move_x < 0:
                        print("Please input a number greater than 0.")
                        continue

                    elif move_y < 0:
                        print("Please input a number greater than 0.")
                        continue

                    temp_coords = []

                    # If the boat direciton is horizontal
                    if direction == "horizontal" or direction == "h":
                        temp_board = copy.deepcopy(board)
                        for i in range(ship_len):
                            if board[move_y][move_x + i] == "x":
                                print(Fore.RED + "Ship intersects another ship.")
                                error = True
                                break
                            temp_board[move_y][move_x + i] = "x"
                            temp_coords.append((move_x + i, move_y))
                            error = False

                    # If the boat direction is vertical
                    elif direction == "vertical" or direction == "v":
                        temp_board = copy.deepcopy(board)
                        for i in range(ship_len):
                            if temp_board[move_y + i][move_x] == "x":
                                print(Fore.RED + "Ship intersects another ship.")
                                error = True
                                break
                            temp_board[move_y + i][move_x] = "x"
                            temp_coords.append((move_x, move_y + i))
                            error = False

                    else:
                        print(Fore.RED + "Please input a ship direction of \"horizontal\" or \"vertical\".")
                        continue

                    # If there was an error
                    if error:
                        error = False
                        continue

                    break

                except ValueError:
                    print(Fore.RED + "Please input valid formatting: \"x, y\"")

                except IndexError:
                    print(Fore.RED + "Ship exited the board. Please try a different placement.")
            if error is False:
                board = temp_board
                ship_coords.append(temp_coords)

        # Send board
        msg = pickle.dumps(board)
        msg = bytes(f"{len(msg):<{HEADERSIZE}}", "utf-8") + msg
        client_socket.send(msg)

        # Send ship locations
        msg = pickle.dumps(ship_coords)
        msg = bytes(f"{len(msg):<{HEADERSIZE}}", "utf-8") + msg
        client_socket.send(msg)

        print_board(board)

        print("Waiting for enemy...\n")

        # Main game loop
        while True:
            won = recieve(pickled=True)
            if won is True:
                if_won(False)
                break

            opponent_board = recieve(pickled=True)
            moves += 1

            powerup = ""
            while True:
                try:
                    # Print the player's guesses and ask for a guess
                    merged_board = merge_board(ship_board=board, player_guess_board=opponent_board)
                    print("\nEnemy's guess board:")
                    print_board(merged_board)
                    print(f"\nYour guess board:")
                    print_board(guess_board)

                    if powerup.lower() == "torpedo":
                        move = input("Input the x coordinate of your torpedo: ")
                    else:
                        print(Fore.GREEN + f"Money: ${money}")
                        move = input("\nEnter a guess (x, y) or type \"shop\" for more options: ")

                    # Shop

                    if move.lower() == "shop":
                        while True:
                            try:
                                print(f"——— SHOP ———\n"
                                      f"Your money: ${money}\n\n")

                                for item in cost:
                                    print(f"{item.capitalize()}: ${cost[item]}")
                                powerup = input("Your powerup: ")

                                if powerup.lower() == "exit":
                                    powerup = ""
                                    break

                                elif cost[powerup.lower()] <= money:
                                    print(Fore.GREEN + f"Successfully bought {powerup.lower()}.")
                                    break

                                else:
                                    print(Fore.RED + f"You do not have enough money to buy that!\n")
                                    continue
                            except KeyError:
                                print(Fore.RED + "Please input a valid powerup. Type \"exit\" to exit.")

                    if powerup.lower() == "torpedo":
                        move_x = int(move.replace(" ", "")) - 1
                        move_y = 0

                    elif powerup.lower() == "bomb":
                        move = input("Input coordiantes of bomb: ")
                        move = move.split(",")
                        move_x = int(move[0].replace(" ", "")) - 1
                        move_y = int(move[1].replace(" ", "")) - 1

                    else:
                        move = move.split(",")
                        move_x = int(move[0].replace(" ", "")) - 1
                        move_y = int(move[1].replace(" ", "")) - 1

                    if powerup == "" and guess_board[move_y][move_x] != empty:
                        print(Fore.RED + "You already guessed that spot!")
                        continue
                    break

                except (ValueError, IndexError):
                    print(Fore.RED + "Please input valid formatting: \"x, y\"")
                    continue

            # Send the powerup to the server
            msg = pickle.dumps(powerup)
            msg = bytes(f"{len(msg):<{HEADERSIZE}}", "utf-8") + msg
            client_socket.send(msg)

            # Send the move to the server
            move_pickle = pickle.dumps((move_x, move_y))
            msg = bytes(f"{len(move_pickle):<{HEADERSIZE}}", "utf-8") + move_pickle
            client_socket.send(msg)

            # Recieve if a ship was sunk
            sunk = recieve(pickled=True)

            # Recieve the result of the move
            result = recieve(pickled=False)
            if result == "hit":
                print(Fore.GREEN + "Hit!")
                hits += 1

            if sunk:
                print(Fore.GREEN + f"You sunk your enemy's {sunk}!\n"*2)

            # Recieve money
            money = recieve(pickled=True)

            # Recieve if you won
            won = recieve(pickled=True)
            if won is True:
                if_won(True)
                break

            # Recieve guess board

            guess_board = recieve(pickled=True)
            print_board(guess_board)

            # Wait for the enemy to execute their turn
            print("Waiting for enemy...")

    except ConnectionResetError:
        print("An existing connection was forcibly closed by the remote host")
        break
