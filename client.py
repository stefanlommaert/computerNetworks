from cgi import test
import re
import socket

ip = socket.gethostbyname('www.tcpipguide.com')
SERVER = ip
PORT = 80
ADDR = (SERVER, PORT)
FORMAT = "utf-8"

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

def send(msg):
    message = msg.encode(FORMAT)
    client.send(message)

msg = "GET / HTTP/1.1\r\nHost:%s\r\n\r\n" % SERVER
send(msg)

response = client.recv(30000).decode(FORMAT)
print(response)
for i in range(len(response)):
    if (response[i:i+14]) == "Content-Length":
        contentLength = int(response[i+16:i+22]) #TODO: slice tot enter begint, niet tot character i+19
        # print(contentLength)
        body = (response[-(contentLength):])

f = open("htmlBody.html", "w")
f.write(body)
f.close()

#open and read the file after the appending:
# f = open("htmlBody.html", "r")
# print(f.read()) 

