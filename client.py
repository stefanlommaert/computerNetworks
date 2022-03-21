import socket

from joblib import PrintTime
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
            "www.linux-ip.net"
            ]


SERVER = SERVERS[4]
PORT = 80
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
        i += 1
    j = 0
    if isChunked(header):
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
        response.append(client.recv(1024))
        # print("received")
    except:
        response = b''.join(response)
        header, body = splitHeader(response)
        # print(chunked)
        body = body.decode("latin-1")
        f = open("htmlBody.html", "w")
        f.write(body)
        f.close()
        response = []
        break



#open and read the file after the appending:
# f = open("htmlBody.html", "r")
# print(f.read()) 




    # except:
    #     response = b''.join(response)
    #     header, body = splitHeader(response)
    #     print(body[:100])
    #     for i in range(len(response)):
    #         if (response[i:i+14]) == "Content-Length":
    #             contentLength = int(response[i+16:i+21]) #TODO: slice tot enter begint, niet tot character i+19
    #             # print(contentLength)
    #             body = (response[-(contentLength):])
    #             f = open("htmlBody.html", "w")
    #             f.write(body)
    #             f.close()
    #     response = []
    #     break
