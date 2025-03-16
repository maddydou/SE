import socket
import random

localIP     = "127.0.0.1"
localPort   = 7500
bufferSize  = 1024
msgFromServer       = "Hello UDP Client"
bytesToSend         = str.encode(msgFromServer)

# Create a datagram socket
UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

# Bind to address and ip
UDPServerSocket.bind((localIP, localPort))

print("UDP server up and listening")

# Listen for incoming datagrams

while(True):
	
	bytesAddressPair = UDPServerSocket.recvfrom(bufferSize)
	message = bytesAddressPair[0]
	address = bytesAddressPair[1]
	clientMsg = "Message from Client:{}".format(message)
	clientIP  = "Client IP Address:{}".format(address)
	
	print(clientMsg)
	print(clientIP)
	
	cMsg = clientMsg[22:]
	cMsg = cMsg[:-1]
	
	if cMsg == "Hello UDP Server":
		print("Hello UDP Client")
	elif cMsg == '202':
		print("Starting...")
	elif cMsg == '221' or cMsg == '222':
		print("Closing Server...")
		break
	else:
		cMsgNum1 = int(cMsg[:-3])
		cMsgNum2 = int(cMsg[3:])
		UDPServerSocket.sendto(str.encode(str(random.randint(203,221))), address)
