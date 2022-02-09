import socket
import pickle
import time
import copy
import colorama
from colorama import Fore

colorama.init(autoreset=True)

HEADERSIZE = 10

IP = input("IP: ")
PORT = int(input("Port: "))

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((IP, PORT))

empty = "—"
board = [[empty for _ in range(10)] for _ in range(10)]
guess_board = [[empty for _ in range(10)] for _ in range(10)]
error = False


def print_board(current_board):  # Prints the board.
    # Print numbers on the x axis
    print("0  ", end="")
    for x in range(len(board)):
        print(x + 1, end="  ")
    print("\n"*0)

    for f in range(len(board)):
        # Print numbers on the y axis
        if f + 1 < 10:
            print(str(f + 1), end="  ")

        elif f + 1 >= 10:
            print(str(f + 1), end=" ")

        # Print board content
        for x in range(len(board)):
            if str(current_board[f][x]) == "x":
                print(Fore.RED + str(current_board[f][x]), end="  ")

            elif str(current_board[f][x]) == "o":
                print(str(current_board[f][x]), end="  ")

            else:
                print(Fore.BLUE + str(current_board[f][x]), end="  ")

        print("\n"*0)


def recieve(pickled):  # Recieve a message
    message_header = client_socket.recv(HEADERSIZE)
    message_length = int(message_header.decode('utf-8').strip())

    if pickled:  # If the message was pickled
        message = client_socket.recv(message_length)
        return pickle.loads(message)

    return client_socket.recv(message_length).decode("utf-8")


if __name__ == "__main__":

    print("Waiting for game to start...")
    start = recieve(pickled=False)
    if start == "game start":

        # Let the user place ships
        ship_lens = [5, 4, 3, 3, 2]
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

                    # If the boat direciton is horizontal
                    if direction == "horizontal":
                        temp_board = copy.deepcopy(board)
                        for i in range(ship_len):
                            if board[move_y][move_x + i] == "x":
                                print("Ship intersects another ship.")
                                error = True
                                break
                            temp_board[move_y][move_x + i] = "x"
                            error = False

                    # If the boat direction is vertical
                    elif direction == "vertical":
                        temp_board = copy.deepcopy(board)
                        for i in range(ship_len):
                            if temp_board[move_y + i][move_x] == "x":
                                print("Ship intersects another ship.")
                                error = True
                                break
                            temp_board[move_y + i][move_x] = "x"
                            error = False

                    else:
                        print("Please input a ship direction of \"horizontal\" or \"vertical\".")
                        continue

                    # If there was an error
                    if error:
                        error = False
                        continue

                    board = temp_board
                    break

                except ValueError:
                    print("Please input valid formatting: \"x, y\"")

                except IndexError:
                    print("Ship exited the board. Please try a different placement.")

        msg = pickle.dumps(board)
        msg = bytes(f"{len(msg):<{HEADERSIZE}}", "utf-8") + msg
        client_socket.send(msg)

        print_board(board)

        print("Waiting for opponent...\n")

        # Main game loop
        while True:
            won = recieve(pickled=True)
            if won:
                opponent_board = recieve(pickled=True)
                print("\nOpponent's board:")
                print_board(opponent_board)
                print("You lose.")
                time.sleep(15)
                exit()

            opponent_board = recieve(pickled=True)
            print("Opponent board recieved.")

            while True:
                try:
                    # Print the player's guesses and ask for another guess
                    print("\n")
                    print("Your ship board:")
                    print_board(board)
                    print()
                    print("Opponent's guess board:")
                    print_board(opponent_board)
                    print()
                    print("Your guess board:")
                    print_board(guess_board)
                    print()
                    move = input("Enter a guess (x, y): ")
                    move = move.split(",")
                    move_x = int(move[0].replace(" ", "")) - 1
                    move_y = int(move[1].replace(" ", "")) - 1

                    if guess_board[move_y][move_x] != empty:
                        print("You already guessed that spot!")
                        continue
                    break

                except (ValueError, IndexError):
                    print("Please input valid formatting: \"x, y\"")

            # Send the move to the server
            move_pickle = pickle.dumps(move)
            msg = bytes(f"{len(move_pickle):<{HEADERSIZE}}", "utf-8") + move_pickle
            client_socket.send(msg)

            # Recieve the result of the move
            result = recieve(pickled=False)
            if result == "hit":
                guess_board[move_y][move_x] = "x"

            else:
                guess_board[move_y][move_x] = "o"

            print_board(guess_board)

            # Recieve if you won
            won = recieve(pickled=True)
            if won:
                opponent_board = recieve(pickled=True)
                print("\nOpponent's board:")
                print_board(opponent_board)
                print("You won!")
                time.sleep(15)
                exit()

            # Wait for the opponent to execute their turn
            print("Waiting for opponent...")
