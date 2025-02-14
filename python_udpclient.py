import socket


msgFromClient       = "Hello UDP Server"
clientNum           = str(msgFromClient)
bytesToSend         = str.encode(clientNum)
serverAddressPort   = ("127.0.0.1", 7500)
bufferSize          = 1024

# Create a UDP socket at client side
UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

# Send to server using created UDP socket
UDPClientSocket.sendto(bytesToSend, serverAddressPort)

running = False
while(True):

	userInput = input("Input ==> ") # todo: replace user input with equipment ids gotten from database upon entry
	                                #       including buttons that start the program, end it, and enter a new network
	print(userInput)
	if userInput == "202" and not running: # start the program
		running = True
		msgFromClient = userInput                                                #   common block for sending information to the server
		UDPClientSocket.sendto(msgFromClient.encode('utf-8'), serverAddressPort) #
		print(bytesToSend)
	elif userInput == "202" and running: # prevent running twice
		print("Program is already running!")
	elif userInput == "222": #code for entering a new network, ports remain constant
		msgFromClient = userInput
		UDPClientSocket.sendto(msgFromClient.encode('utf-8'), serverAddressPort)
		newNetwork = input("New Network ==> ")
		serverAddressPort = (newNetwork, 7501)
	elif userInput == "221": # kill the program
		msgFromClient = userInput
		UDPClientSocket.sendto(msgFromClient.encode('utf-8'), serverAddressPort)
		running = False
		break
	else: # send signal to turn on device of user input id
		msgFromClient = userInput
		equipAddress = (serverAddressPort[0], int(userInput))
		UDPClientSocket.sendto(msgFromClient.encode('utf-8'), equipAddress)