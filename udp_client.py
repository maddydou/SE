import socket

def send_equipment_id(equip_id, server_address=("127.0.0.1", 7500)):
    """
    Sends the given equipment id as a UDP message to the specified server address.
    """
    UDPClientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    message = str(equip_id)
    UDPClientSocket.sendto(message.encode('utf-8'), server_address)
    UDPClientSocket.close()
