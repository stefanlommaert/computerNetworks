import socket
from PIL import Image
import io
from bs4 import BeautifulSoup
# https://www.geeks3d.com/hacklab/20190110/python-3-simple-http-request-with-the-socket-module/
# www.example.com
# www.google.com
# www.tcpipguide.com
# www.tinyos.net
# www.linux-ip.net

SERVERS =   [
            "www.example.com",
            "www.google.com",
            "www.tcpipguide.com",
            "www.tinyos.net",
            "www.linux-ip.net",
            ]


SERVER = SERVERS[4]
SERVER = "0.0.0.0"
# PORT = 80
PORT = 4200
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


def splitHeader(msg):
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
    if isChunked(header):
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


msg = "GET / HTTP/1.1\r\nHost:%s\r\n\r\n" % SERVER

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
        header, body = splitHeader(response)
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
    send(msg)
    while True:
        try:
            client.settimeout(0.5)
            response.append(client.recv(10000))
            # print(response)
        except:
            response = b''.join(response)
            header, body = splitHeader(response)
            print(image, "saving")
            try:
                img = Image.open(io.BytesIO(body))
                img.save("images/%s.png" %title)
            except:
                print(image, "requested URL not found")
            title += 1
            response = []
            # print(image, "saved")

            break



#open and read the file after the appending:
# f = open("htmlBody.html", "r")
# print(f.read()) 