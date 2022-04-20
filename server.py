"""
 Implements a simple HTTP/1.1 Server

"""

from email.utils import formatdate
import socket
from _thread import *
import threading
from PIL import Image
import io
import os
import time

# Custom class for 400 Bad Request Exception
class BadRequestError(Exception):
    pass

# Custom class for 304 Not Modified Exception
class NotModifiedSinceError(Exception):
    pass

# Checks if the given file has been modified after the given "if-modified-since:" date."
def isModifiedSince(filename, headers):
    modifiedFileTime = os.path.getmtime('server'+filename)
    modifiedFileTime = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(modifiedFileTime))
    for headerName in headers:
        if "if-modified-since:" in headerName.lower():
            requestedTime = headerName.lower().split('if-modified-since:')[1].lstrip()
            modifiedFileTime = modifiedFileTime.lower()

            requestedTime = time.strptime(requestedTime,'%a, %d %b %Y %H:%M:%S gmt')
            modifiedFileTime = time.strptime(modifiedFileTime,'%a, %d %b %Y %H:%M:%S gmt')
            if requestedTime > modifiedFileTime:
                return False
            else:
                return True
    return True

# Main function for GET and HEAD request. 
def GET(isHeadCommand, headers, modifiedSince):
    filename = headers[0].split()[1]
    contentType = 'text/html; charset=UTF-8'
    if filename == '/':
        filename = '/index.html'
    if modifiedSince:
        if not isModifiedSince(filename, headers):
            raise NotModifiedSinceError     

    if filename == "/gandhalf.jpg":
        im = Image.open('server/gandhalf.jpg')
        buf = io.BytesIO()
        im.save(buf, format='JPEG')
        content = buf.getvalue()
        contentType = 'image/png'
    else:
        fin = open('server'+filename)
        content = fin.read().encode()
        fin.close()
    contentLength = str(len(content))
    date = formatdate(timeval=None, localtime=False, usegmt=True)
    if isHeadCommand:
        HEADER = 'HTTP/1.1 200 OK\r\nDate: %s\r\nContent-Length: %s\r\nContent-Type: %s\r\n\r\n' %(date, contentLength, contentType)
        return HEADER.encode()
    else:
        HEADER = 'HTTP/1.1 200 OK\r\nDate: %s\r\nContent-Length: %s\r\nContent-Type: %s\r\n\r\n' %(date, contentLength, contentType)
        return HEADER.encode() + content

# Main function for handling PUT request
def PUT(headers, body):
    filename = headers[0].split()[1]
    filename = filename.split(".")[0]
    newFileCreated = False
    newContent = False
    try:
        f = open("server/put_post_files"+filename+".txt", "x") # Returns error if file already exists.
        newFileCreated = True
    except:
        f = open("server/put_post_files"+filename+".txt", "r")
        oldContent = f.read()
        if body != oldContent:
            newContent = True
        f.close()
        f = open("server/put_post_files"+filename+".txt", "w")
    f.write(body)
    f.close()
    contentLength = 0
    date = formatdate(timeval=None, localtime=False, usegmt=True)
    contentType = 'text/html; charset=UTF-8'
    if newFileCreated:
        HEADER = 'HTTP/1.1 201 Created\r\nContent-Location: %s.txt\r\nDate: %s\r\nContent-Length: %s\r\nContent-Type: %s\r\n\r\n' %(filename, date, contentLength, contentType)
    elif newContent:
        HEADER = 'HTTP/1.1 200 OK\r\nContent-Location: %s.txt\r\nDate: %s\r\nContent-Length: %s\r\nContent-Type: %s\r\n\r\n' %(filename, date, contentLength, contentType)
    else:
        HEADER = 'HTTP/1.1 204 No Content\r\nContent-Location: %s.txt\r\nDate: %s\r\nContent-Length: %s\r\nContent-Type: %s\r\n\r\n' %(filename, date, contentLength, contentType)
    return HEADER.encode() 
        
# Main function for handling POST request
def POST(headers, body):
    filename = headers[0].split()[1]
    filename = filename.split(".")[0]
    newFileCreated = False
    try:
        f = open("server/put_post_files"+filename+".txt", "x") # Returns error if file already exists.
        newFileCreated = True
    except:
        f = open("server/put_post_files"+filename+".txt", "a")

    f.write(body)
    f.close()
    contentLength = 0
    date = formatdate(timeval=None, localtime=False, usegmt=True)
    contentType = 'text/html; charset=UTF-8'
    if newFileCreated:
        HEADER = 'HTTP/1.1 201 Created\r\nContent-Location: %s.txt\r\nDate: %s\r\nContent-Length: %s\r\nContent-Type: %s\r\n\r\n' %(filename, date, contentLength, contentType)
    else:
        HEADER = 'HTTP/1.1 200 OK\r\nContent-Location: %s.txt\r\nDate: %s\r\nContent-Length: %s\r\nContent-Type: %s\r\n\r\n' %(filename, date, contentLength, contentType)
    return HEADER.encode() 

# Threaded function to handle multiple client requests
def threaded(client_connection):
    while True:
        try:
            request = client_connection.recv(2048).decode()
            print(request)
            if request == "":
                raise BadRequestError

            contentLength = 0
            date = formatdate(timeval=None, localtime=False, usegmt=True)
            contentType = 'text/html; charset=UTF-8'
            
            body = ""
            header, body = request.split('\r\n\r\n')[0], body.join(request.split('\r\n\r\n')[1:])
            headers = header.split('\r\n')
            command = headers[0].split()[0]
            hasHostHeader = False
            closeConnection = False
            modifiedSince = False
            for headerName in headers:
                if "host:" in headerName.lower():
                    hasHostHeader = True
                if "connection: close" in headerName.lower():
                    closeConnection = True
                if "if-modified-since:" in headerName.lower():
                    modifiedSince = True
            if not hasHostHeader:
                raise BadRequestError
            if command == "GET":
                response = GET(False, headers, modifiedSince)
            if command == "HEAD":
                response = GET(True, headers, modifiedSince)
            if command == "PUT":
                response = PUT(headers, body)
            if command == "POST":
                response = POST(headers, body)
            client_connection.send(response)
            
            if closeConnection:
                client_connection.close()
                return
        except FileNotFoundError:
            HEADER = 'HTTP/1.1 404 Not Found\r\nDate: %s\r\nContent-Length: %s\r\nContent-Type: %s\r\n\r\n'%(date, contentLength, contentType)
            client_connection.send(HEADER.encode())
        except BadRequestError:
            HEADER = 'HTTP/1.1 400 Bad Request\r\nDate: %s\r\nContent-Length: %s\r\nContent-Type: %s\r\n\r\n'%(date, contentLength, contentType)
            client_connection.send(HEADER.encode())
        except NotModifiedSinceError:
            HEADER = 'HTTP/1.1 304 Not Modified\r\nDate: %s\r\nContent-Length: %s\r\nContent-Type: %s\r\n\r\n'%(date, contentLength, contentType)
            client_connection.send(HEADER.encode())
        except ConnectionAbortedError:
            print("connection closed to client")
            return
        except ConnectionResetError:
            print("connection closed to client")
            return
        except Exception as e:
            print("error:", e)
            HEADER = 'HTTP/1.1 500 Internal Server Error\r\n'%(date, contentLength, contentType)
            client_connection.send(HEADER.encode())



def main():
    # Define socket host and port
    SERVER_HOST = '192.168.1.114'
    SERVER_PORT = 80

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(1)
    print('Listening on port %s ...' % SERVER_PORT)
    while True:    
        # Wait for client connections
        client_connection, client_address = server_socket.accept()
        print('Connected to :', client_address[0], ':', client_address[1])
        threading.Thread(target=threaded, args=(client_connection,)).start()
    server_socket.close()


if __name__ == '__main__':
    main()
