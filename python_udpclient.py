import socket

def send_equipment_id(equip_id, server_address=("127.0.0.1", 7500)):
    """
    Sends the given equipment id as a UDP message to the specified server address.
    """
    UDPClientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    message = str(equip_id)
    UDPClientSocket.sendto(message.encode('utf-8'), server_address)
    UDPClientSocket.close()

if __name__ == '__main__':
    msgFromClient = "Hello UDP Server"
    bytesToSend = str.encode(msgFromClient)
    serverAddressPort = ("127.0.0.1", 7500)
    bufferSize = 1024

    # Create a UDP socket at client side
    UDPClientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Send an initial test message
    UDPClientSocket.sendto(bytesToSend, serverAddressPort)

    running = False
    while True:
        userInput = input("Input ==> ")  # For testing purposes.
        print(userInput)
        if userInput == "202" and not running:
            running = True
            UDPClientSocket.sendto(userInput.encode('utf-8'), serverAddressPort)
            print(bytesToSend)
        elif userInput == "202" and running:
            print("Program is already running!")
        elif userInput == "222":  # Code for entering a new network.
            UDPClientSocket.sendto(userInput.encode('utf-8'), serverAddressPort)
            newNetwork = input("New Network ==> ")
            serverAddressPort = (newNetwork, 7501)
        elif userInput == "221":  # Kill the program.
            UDPClientSocket.sendto(userInput.encode('utf-8'), serverAddressPort)
            running = False
            break
        else:  # Send signal to turn on device of user input id.
            equipAddress = (serverAddressPort[0], int(userInput))
            UDPClientSocket.sendto(userInput.encode('utf-8'), equipAddress)
