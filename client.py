import chunk
import socket
from PIL import Image
import io
from bs4 import BeautifulSoup

# Send message to client.
def send(client, msg):
    message = msg.encode("ISO-8859-1")
    client.send(message)

# Checks if the head has the "Transfer-Encoding: chunked" header.
def isChunked(header):
    for i in range(len(header)):
            if (header[i:i+26]) == b"Transfer-Encoding: chunked":
                return True
    return False

# Returns the head and body of the message.
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
                body = body[j+2:] #slices the chunksize off the body
                chunkSize = int(chunkSize, 16) #change hexadecimal value to decimal integer
                if chunkSize==0:
                    finalChunk=True
                totalBody+=body[:chunkSize]
                body = body[chunkSize+2:] 
                j = 0

            j += 1
    return header, totalBody

# Checks if the message has been fully received.
def isFullySend(msg):
    splitMsg = msg.split(b"\r\n\r\n")
    if len(splitMsg) <= 1:
        return False
    head, body = splitMsg[0], b''.join(splitMsg[1:])

    contentLength = 0
    for header in head.split(b'\r\n'):
        if b"content-length:" in header.lower():
            contentLength = int(header.lower().split(b"content-length:")[1])
        if b"transfer-encoding:" in header.lower() and b"chunked" in header.lower():
            splitBody = body.split(b'\r\n')
            if splitBody[len(splitBody)-1] == b'0':
                return True
            else:
                return False
        
    if len(body)>= contentLength:
        return True
    else:
        return False

# Main function for receiving server response, and storing it
def receive(client, COMMAND):
    response = b''
    decodingFormat = "ISO-8859-1" # HTTP 1.1 default decoding format if none is specified
    # decodingFormat = "UTF-8"

    while True:
        try:
            client.settimeout(10)
            data = client.recv(2048)
            response += data
            if "HEAD" in COMMAND:
                print(response)
                f = open("htmlBody.html", "w")
                body = ""
                f.write(body)
                f.close()
                break
            elif isFullySend(response):
                header, body = splitHeader(response, COMMAND)
                headers = header.decode().split("\r\n")
                print(header)

                # Get decoding format if given, otherwise use default "ISO-8859-1" format.
                for headerName  in headers:
                    if "charset=" in headerName.lower():
                        decodingFormat = headerName.lower().split("charset=")[1]
                        # print("FORMAT: ", decodingFormat)
                body = body.decode(decodingFormat)

                # Save content of body on HTML file
                f = open("htmlBody.html", "w")
                f.write(body)
                f.close()

                break
        except TimeoutError: # If server does not respond after 10 seconds, try again.
            print("time out")
            
        except Exception as e:
            print(e)
            break

# Main code for receiving image data and saving them.
def findImages(client, SERVER, COMMAND, PORT):
    f = open("htmlBody.html", "r")
    images = []
    soup = BeautifulSoup(f, features="html.parser")
    title = 0
    for img in soup.findAll('img'):
        images.append(img.get('src'))
        img["src"] = img["src"].replace(img.get('src'), "images/%s.png" %title) #replace image source with own path
        title += 1
    f = open("htmlBody.html", "w")
    f.write(str(soup))
    f.close()
    title = 0

    # Request image data from specified servers
    sortedImages = []

    # Sort images so that images on the same server appear at the front of the list, and images on different servers at the end.
    for image in images:
        if "www." in image:
            sortedImages.append(image)
        else:
            sortedImages.insert(0,image)

    for image in sortedImages:
        resource = image

        # checks if image is on other server, if so: make a connection to the new server
        if "www." in image:
            newImage = image.replace("https://", "").replace("http://", "") #remove http from url
            SERVER = newImage.split("/")[0]
            resource = newImage.replace(SERVER, "")
            print(image," found on server: ", SERVER)
            client.close()
            ADDR = (SERVER, PORT)
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(ADDR)


        msg = "GET /%s HTTP/1.1\r\nHost:%s\r\n\r\n" %(resource, SERVER)
        send(client, msg)
        response = b''
        while True:
            try:
                client.settimeout(10)
                data = client.recv(1024)
                response += data
                if isFullySend(response):
                    header, body = splitHeader(response, COMMAND)
                    try:
                        title = images.index(image)
                        images[title] = None # in case of duplicate images, remove one of the duplicates
                        img = Image.open(io.BytesIO(body))
                        img.save("images/%s.png" %title)
                        print(image, " saved")

                    except Exception as e:
                        print(image, "requested URL not found")
                    title += 1
                    response = []
                    break
            except TimeoutError:
                print("time out")
            except Exception as e:
                print(e)
                break

def main():

    SERVERS =   [
                "www.example.com",
                "www.google.com",
                "www.tcpipguide.com",
                "www.tinyos.net",
                "www.linux-ip.net",
                '192.168.1.114', #ip adress of own server
                ]

    # COMMAND = "GET"
    # SERVER = SERVERS[5]
    # PORT = 5055

    # COMMAND = "GET /"
    # SERVER = SERVERS[1]
    # PORT = 80

    COMMAND = input("HTTP command: ")
    SERVER = input("URI: ")
    PORT = int(input("Port: ") or 80)
    ADDR = (SERVER, PORT)
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)

    if "PUT" in COMMAND or "POST" in COMMAND:
        REQUEST = input("PUT/POST request: ")
        msg = "%s HTTP/1.1\r\nHost:%s\r\n\r\n%s" %(COMMAND, SERVER, REQUEST)
    else:
        # msg = "%s HTTP/1.1\r\nHost:%s\r\nIf-Modified-Since: Wed, 27 Apr 2022 12:16:00 GMT\r\n\r\n" %(COMMAND, SERVER)
        msg = "%s HTTP/1.1\r\nHost:%s\r\n\r\n" %(COMMAND, SERVER)
    send(client, msg)

    receive(client, COMMAND)

    # CHeck if there are images in the html body, if so: send a request to the server which has the images stored.
    f = open("htmlBody.html", "r")
    soup = BeautifulSoup(f, features="html.parser")
    f.close()
    if len(soup.findAll('img')) > 0:
        findImages(client, SERVER, COMMAND, PORT)


if __name__ == '__main__':
    main()