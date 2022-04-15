import socket
from PIL import Image
import io
from bs4 import BeautifulSoup
# https://www.geeks3d.com/hacklab/20190110/python-3-simple-http-request-with-the-socket-module/

# TODO:
# get images not on same server
# apply not received protocol, ask again
# Content-Type: text/html; charset=ISO-8859-1 implementeren
# case incensitive headers

SERVERS =   [
            "www.example.com",
            "www.google.com",
            "www.tcpipguide.com",
            "www.tinyos.net",
            "www.linux-ip.net",
            '192.168.1.114',
            ]

COMMAND = "GET"
SERVER = SERVERS[5]
PORT = 5055

# COMMAND = "GET"
# SERVER = SERVERS[3]
# PORT = 80

# COMMAND = input("HTTP command: ")
# SERVER = input("URI: ")
# PORT = int(input("Port: ") or 80)
ADDR = (SERVER, PORT)
FORMAT = "utf-8"
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

def send(msg):
    message = msg.encode(FORMAT)
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

if COMMAND == "PUT" or COMMAND == "POST":
    REQUEST = input("PUT/POST request: ")
    msg = "%s /testT.txt HTTP/1.1\r\nHost:%s\r\n\r\n%s" %(COMMAND, SERVER, REQUEST)
else:
    msg = "%s / HTTP/1.1\r\nHost:%s\r\n\r\n" %(COMMAND, SERVER)
print("send: ", msg)
send(msg)
response = []
while True:
    try:
        client.settimeout(1)
        data = client.recv(10000)
        if data == b"":
            raise Exception("Receiving empty data")
        response.append(data)
    except:
        response = b''.join(response)
        print(response)
        header, body = splitHeader(response, COMMAND)
        body = body.decode("latin-1")
        f = open("htmlBody.html", "w")
        f.write(body)
        f.close()
        response = []
        break

response = []
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
    print("image send: ", msg)
    send(msg)
    while True:
        try:
            client.settimeout(1)
            response.append(client.recv(10000))
        except:
            response = b''.join(response)
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