import socket
import pickle
import time
import threading

empty = "—"
client1_guess_board = [[empty for _ in range(10)] for _ in range(10)]
client2_guess_board = [[empty for _ in range(10)] for _ in range(10)]

HEADERSIZE = 10

IP = "192.168.1.12"
PORT = 1234

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind((IP, PORT))
server_socket.listen(2)

clients = []

turn = "client1"


def recieve(client_socket, pickled):  # Recieve a message
    message_header = client_socket.recv(HEADERSIZE)
    message_length = int(message_header.decode('utf-8').strip())

    if pickled:  # If the message was pickled
        message = client_socket.recv(message_length)
        if message is False:
            clients.remove(client_socket)
            print("Client disconnected.")

        return pickle.loads(message)

    message = client_socket.recv(message_length).decode("utf-8")
    if message is False:
        clients.remove(client_socket)
        print("Client disconnected.")


def send(client_socket, message, pickled):
    try:
        if pickled:
            message = pickle.dumps(message)
            message = f"{len(message):<{HEADERSIZE}}".encode("utf-8") + message
            client_socket.send(message)

        else:
            message = message.encode("utf-8")
            message = f"{len(message):<{HEADERSIZE}}".encode("utf-8") + message
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
    if current_board[y][x] == "x":
        return "hit"
    return "miss"


def win_check(current_board, guess_board):  # Check if the client won
    for i in range(len(current_board)):
        for x in range(len(current_board)):
            if guess_board[i][x] == empty and current_board[i][x] == "x":
                return False
    return True


def turns(client_socket, client_guess_board, opponent_board, opponent_guess_board,
          opponent_client_socket, client_board):
    # Notify the client it is their turn
    send(client_socket, opponent_guess_board, True)

    # Recieve the client's move
    move = recieve(pickled=True, client_socket=client_socket)

    client_move_x = int(move[0].replace(" ", "")) - 1
    client_move_y = int(move[1].replace(" ", "")) - 1

    # Check if the cient's move is a hit and send the result back
    hit = check_hit(client_move_x, client_move_y, opponent_board)

    if hit == "hit":
        client_guess_board[client_move_y][client_move_x] = "x"
    else:
        client_guess_board[client_move_y][client_move_x] = "o"

    send(client_socket, hit, False)

    # Return if client won
    win = win_check(opponent_board, client_guess_board)

    for clients_socket in clients:
        send(clients_socket, win, True)

    # If the client won, send each other's ship placements
    if win_check(opponent_board, client_guess_board):
        # Send to client socket
        send(client_socket, opponent_board, True)

        # Send to opponent client socket
        send(opponent_client_socket, client_board, True)

    return client_guess_board


if __name__ == "__main__":
    t = threading.Thread(target=manage_clients)
    t.start()

    # Wait for players to connect

    print("Waiting for players to connect.")
    while len(clients) < 2:
        time.sleep(1)

    while True:
        # Notify clients to start the game

        msg = "game start".encode("utf-8")
        msg = f"{len(msg):<{HEADERSIZE}}".encode("utf-8") + msg

        for client in clients:
            client.send(msg)

        # Recieve the player's battleship placements

        client1_socket = clients[0]
        client2_socket = clients[1]

        client1_board = recieve(client1_socket, True)
        client2_board = recieve(client2_socket, True)

        # Send to client 1 if they won (the client is expecting this information)
        send(client1_socket, win_check(client1_board, client1_guess_board), True)

        # Main game loop
        while True:
            # Handle client 1's turn
            if turn == "client1":
                turn = "client2"
                client1_guess_board = turns(client1_socket, client1_guess_board, client2_board,
                                            client2_guess_board, client2_socket, client1_board)

                # If the client won, reset game
                if win_check(client2_board, client1_guess_board):
                    turn = "client1"
                    client1_guess_board = [[empty for _ in range(10)] for _ in range(10)]
                    client2_guess_board = [[empty for _ in range(10)] for _ in range(10)]
                    time.sleep(10)
                    break

            elif turn == "client2":
                # Handle client 2's turn
                turn = "client1"
                client2_guess_board = turns(client2_socket, client2_guess_board, client1_board,
                                            client1_guess_board, client1_socket, client2_board)

                # If the client won, reset game
                if win_check(client1_board, client2_guess_board):
                    client1_guess_board = [[empty for _ in range(10)] for _ in range(10)]
                    client2_guess_board = [[empty for _ in range(10)] for _ in range(10)]
                    time.sleep(10)
                    break
