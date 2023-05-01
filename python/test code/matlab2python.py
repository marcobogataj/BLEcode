import socket 
import struct

# Create a UDP socket
sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP

# Bind the socket to the port
UDP_IP = '0.0.0.0'
UDP_PORT = 2
server_address = (UDP_IP, UDP_PORT)
print('starting up on {} port {}'.format(*server_address))
sock.bind(server_address)
msgcount = 0

while True:
    #print('\nwaiting to receive message')
    data, address = sock.recvfrom(512)
    print('received {} bytes from {}'.format(len(data), address))
    output = struct.unpack('d',data)
    msgcount += 1
    print("received message:", output)
    print("message count:", str(msgcount))
    
    


