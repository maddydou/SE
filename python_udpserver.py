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

playerscorelist = [] # format: { equipment id, hit other base?, score }
# initialize array

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
	
	equipment = True
	for i in range(len(cMsg)):
		if cMsg[i] == ':':
			equipment = False
	
	if cMsg == "Hello UDP Server":
		print("Hello UDP Client")
	elif cMsg == '202':
		print("Starting...")
	elif cMsg == '221' or cMsg == '222':
		print("Closing Server...")
		break
	elif equipment:
		playerscorelist.append({ cMsg, False, 0 })
	else:
		equipment = True
		
		cMsgNum1 = int(cMsg[:-3])
		cMsgNum2 = int(cMsg[3:])
		
		if cMsgNum2 == 53 and cMsgNum1 % 2 == 1:
			# code for Red team hitting other base
			for i in range(len(playerscorelist)):
				if playerscorelist[i][0] == cMsgNum1:
					playerscorelist[i][1] == true
		elif cMsgNum2 == 43 and cMsgNum1 % 2 == 0:
			# code for Green team hitting other base
			for i in range(len(playerscorelist)):
				if playerscorelist[i][0] == cMsgNum1:
					playerscorelist[i][1] == true
		elif (cMsgNum1 % 2 == 0 and cMsgNum2 % 2 == 0) or (cMsgNum1 % 2 == 1 and cmsgNum2 % 2 == 1):
			# code for deducting 10 points from cMsgNum1 player
			for i in range(len(playerscorelist)):
				if playerscorelist[i][0] == cMsgNum1:
					if playerscorelist[i][2] != 0:
						playerscorelist[i][2] == playerscorelist[i][2] - 10;
		else:
			# code for adding 10 points to cMsgNum1 player
			for i in range(len(playerscorelist)):
				if playerscorelist[i][0] == cMsgNum1:
					playerscorelist[i][2] == playerscorelist[i][2] + 10;
		# UDPServerSocket.sendto(str.encode(str(random.randint(203,221))), address)
