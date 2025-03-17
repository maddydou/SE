import socket
import time
import sys
import os

def send_equipment_id(equip_id, server_address=("127.0.0.1", 7500)):
    """
    Sends the given equipment id as a UDP message to the specified server address.
    """
    UDPClientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    message = str(equip_id)
    UDPClientSocket.sendto(message.encode('utf-8'), server_address)
    UDPClientSocket.close()

msgFromClient = "Hello UDP Server"
bytesToSend = str.encode(msgFromClient)
serverAddressPort = ("127.0.0.1", 7500)
bufferSize = 1024

clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
playerAddressPort = ("127.0.0.1", 7501)
clientSocket.connect(playerAddressPort)

# Create a UDP socket at client side
UDPClientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
# Send an initial test message
UDPClientSocket.sendto(bytesToSend, serverAddressPort)

running = False
while True:
	# make able to receive information from the main process
	userInput = clientSocket.recv(bufferSize)
	userInput = userInput.decode()
	
	if userInput == "202" and not running:
		running = True
		UDPClientSocket.sendto(userInput.encode('utf-8'), serverAddressPort)
		print(bytesToSend)
	elif userInput == "202" and running:
		print("Program is already running!")
	elif userInput == "222":  # Code for entering a new network.
		UDPClientSocket.sendto(userInput.encode('utf-8'), serverAddressPort)
		newNetwork = clientSocket.recv(bufferSize)
		newNetwork = newNetwork.decode()
		playerAddressPort = (newNetwork, 7501)
	elif userInput == "221":  # Kill the program.
		UDPClientSocket.sendto(userInput.encode('utf-8'), serverAddressPort)
		running = False
		break
	elif userInput == "":
		time.sleep(0.01)
	else:  # Send signal to turn on device of user input id.
		equipAddress = (serverAddressPort[1], int(userInput))
		UDPClientSocket.sendto(userInput.encode('utf-8'), equipAddress)
