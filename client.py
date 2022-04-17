import socket
from PIL import Image
import io
from bs4 import BeautifulSoup
# https://www.geeks3d.com/hacklab/20190110/python-3-simple-http-request-with-the-socket-module/

# TODO:
# get images not on same server
def send(client, msg):
    message = msg.encode("ISO-8859-1")
    client.send(message)

def isChunked(header):
    for i in range(len(header)):
            if (header[i:i+26]) == b"Transfer-Encoding: chunked":
                return True
    return False

def splitHeader(msg, COMMAND):
    header = b""
    body = b""
    totalBody = b""
    finalChunk = False
    i = 0
    while header==b"":
        if (msg[i:i+4]) == b"\r\n\r\n":
            header = msg[:i]
            totalBody = msg[i+4:]
            body = totalBody
        i += 1
    j = 0
    if isChunked(header) and not COMMAND=="HEAD":
        totalBody = b""
        while finalChunk == False:
            if (body[j:j+2]) == b"\r\n":
                chunkSize = body[:j]
                body = body[j+2:]
                chunkSize = int(chunkSize, 16)
                if chunkSize==0:
                    finalChunk=True
                totalBody+=body[:chunkSize]
                body = body[chunkSize+2:]
                j = 0

            j += 1
    return header, totalBody

def isFullySend(msg):
    splitMsg = msg.split(b"\r\n\r\n")
    if len(splitMsg) <= 1:
        return False
    head, body = splitMsg[0], b''.join(splitMsg[1:])

    contentLength = 0
    for header in head.split(b'\r\n'):
        if b"content-length:" in header.lower():
            contentLength = int(header.lower().split(b"content-length:")[1])
        if b"content-type:" in header.lower() and b"chunked" in header.lower():
            totalBody = b""
            j = 0
            while True:
                try:
                    if (body[j:j+2]) == b"\r\n":
                        chunkSize = body[:j]
                        body = body[j+2:]
                        chunkSize = int(chunkSize, 16)
                        if chunkSize==0:
                            return True
                        totalBody+=body[:chunkSize]
                        body = body[chunkSize+2:]
                        j = 0

                    j += 1
                except:
                    return False

            # newBody = body
            # totalBody = b''
            # while True:
            #     chunkLength = newBody.split('\r\n')[0]
            #     newBody = b''.join(newBody.split('\r\n')[1:])

    if len(body)>= contentLength:
        return True
    else:
        return False

def receive(client, COMMAND):
    response = b''
    decodingFormat = "ISO-8859-1"
    while True:
        try:
            client.settimeout(10)
            data = client.recv(100)
            if data == b"":
                raise Exception("Receiving empty data")
            response += data
            print(isFullySend(response))
            if isFullySend(response):
                raise Exception
        except TimeoutError:
            print("time out")
        except:
            header, body = splitHeader(response, COMMAND)
            headers = header.decode().split("\r\n")
            for headerName  in headers:
                if "charset=" in headerName.lower():
                    decodingFormat = headerName.lower().split("charset=")[1]
            # print("FORMAT: ", decodingFormat)
            body = body.decode(decodingFormat)
            f = open("htmlBody.html", "w")
            f.write(body)
            f.close()
            response = []
            break

def findImages(client, SERVER, COMMAND):
    f = open("htmlBody.html", "r")
    images = []
    soup = BeautifulSoup(f, features="html.parser")
    title = 0
    for img in soup.findAll('img'):
        images.append(img.get('src'))
        img["src"] = img["src"].replace(img.get('src'), "images/%s.png" %title)
        title += 1
    f = open("htmlBody.html", "w")
    f.write(str(soup))
    f.close()
    title = 0
    for image in images:
        msg = "GET /%s HTTP/1.1\r\nHost:%s\r\n\r\n" %(image, SERVER)
        send(client, msg)
        response = b''
        while True:
            try:
                client.settimeout(1)
                data = client.recv(10000)
                response += data
                if isFullySend(response):
                    raise Exception
            except TimeoutError:
                print("time out")
            except:
                header, body = splitHeader(response, COMMAND)
                try:
                    img = Image.open(io.BytesIO(body))
                    img.save("images/%s.png" %title)
                    print(image, " saved")

                except:
                    print(image, "requested URL not found")
                title += 1
                response = []
                break

def main():

    SERVERS =   [
                "www.example.com",
                "www.google.com",
                "www.tcpipguide.com",
                "www.tinyos.net",
                "www.linux-ip.net",
                '192.168.1.114',
                ]

    # COMMAND = "GET"
    # SERVER = SERVERS[5]
    # PORT = 5055

    COMMAND = "GET"
    SERVER = SERVERS[1]
    PORT = 80

    # COMMAND = input("HTTP command: ")
    # SERVER = input("URI: ")
    # PORT = int(input("Port: ") or 80)
    ADDR = (SERVER, PORT)
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)

    if COMMAND == "PUT" or COMMAND == "POST":
        REQUEST = input("PUT/POST request: ")
        msg = "%s /testT.txt HTTP/1.1\r\nHost:%s\r\n\r\n%s" %(COMMAND, SERVER, REQUEST)
    else:
        msg = "%s / HTTP/1.1\r\nHost:%s\r\n\r\n" %(COMMAND, SERVER)
    send(client, msg)
    receive(client, COMMAND)
    f = open("htmlBody.html", "r")
    soup = BeautifulSoup(f, features="html.parser")
    f.close()
    if len(soup.findAll('img')) > 0:
        findImages(client, SERVER, COMMAND)



if __name__ == '__main__':
    main()