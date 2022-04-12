"""
 Implements a simple HTTP/1.1 Server

"""

from email.utils import formatdate
import socket
from _thread import *
import threading
from PIL import Image
import io

class BadRequestError(Exception):
    pass

def GET(request, headers):
    filename = headers[0].split()[1]
    print(filename)
    if filename == '/':
        filename = '/index.html'
        fin = open('server'+filename)
        content = str.encode(fin.read())
        fin.close()
    else:
        im = Image.open('server/gandhalf.jpg')
        buf = io.BytesIO()
        im.save(buf, format='JPEG')
        content = buf.getvalue()
        
    return content

def HEADER():
    pass

def PUT():
    pass

def POST():
    pass

def threaded(client_connection):
    try:
        while True:
            request = client_connection.recv(1024).decode()
            print(request)
            header = request.split('\r\n\r\n')[0]
            headers = header.split('\r\n')
            hasHostHeader = False
            for headerName in headers:
                if "Host: " in headerName:
                    hasHostHeader = True
            if not hasHostHeader:
                raise BadRequestError
            if headers[0].split()[0] == "GET":
                content = GET(request, headers)

            contentLength = str(len(content))
            date = formatdate(timeval=None, localtime=False, usegmt=True)
            HEADER = 'HTTP/1.1 200 OK\r\nDate: %s\r\nContent-Length: %s\r\n\r\n' %(date, contentLength)
            response = str.encode(HEADER) + content
            client_connection.send(response)
            # client_connection.send(response.encode())
            # client_connection.close()
            # return
    except FileNotFoundError:
        HEADER = 'HTTP/1.1 404 Not Found\r\n'
        client_connection.send(HEADER.encode())
    except BadRequestError:
        HEADER = 'HTTP/1.1 400 Bad Request\r\n'
        client_connection.send(HEADER.encode())
    except Exception as e:
        print(e)
        HEADER = 'HTTP/1.1 500 Internal Server Error\r\n'
        client_connection.send(HEADER.encode())



# Create socket
def main():
    # Define socket host and port
    SERVER_HOST = '192.168.1.114'
    SERVER_PORT = 5055

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(1)
    print('Listening on port %s ...' % SERVER_PORT)
    while True:    
        # Wait for client connections
        client_connection, client_address = server_socket.accept()
        print('Connected to :', client_address[0], ':', client_address[1])
        threading.Thread(target=threaded, args=(client_connection,)).start()
    server_socket.close()

# Close socket

if __name__ == '__main__':
    main()
