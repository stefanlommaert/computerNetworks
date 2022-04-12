"""
 Implements a simple HTTP/1.0 Server

"""

import socket
import time
from _thread import *
import threading


def threaded(client_connection):
    while True:
 
        # Get the client request
        request = client_connection.recv(1024).decode()
        print(request)
        # Get the content of htdocs/index.html
        fin = open('server/index.html')
        content = fin.read()
        fin.close()

        # Send HTTP response
        response = 'HTTP/1.0 200 OK\n\n' + content
        client_connection.send(response.encode())
        # time.sleep(10)
        # client_connection.close()
        # return



# Create socket
def main():
    # Define socket host and port
    SERVER_HOST = '0.0.0.0'
    # SERVER_HOST = '192.168.1.114'
    SERVER_PORT = 4200

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(1)
    print('Listening on port %s ...' % SERVER_PORT)
    while True:    
        # Wait for client connections
        client_connection, client_address = server_socket.accept()
        print('Connected to :', client_address[0], ':', client_address[1])
        # start_new_thread(threaded, (client_connection,))
        threading.Thread(target=threaded, args=(client_connection,)).start()
    server_socket.close()

# Close socket

if __name__ == '__main__':
    main()
