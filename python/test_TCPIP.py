import asyncio
import socket
import time
import struct
import json
from helper_functions import setup_logging
from pynput import keyboard
import sys

"""TO DO
Test delay with TCP/IP between Python and Simulink with simple code and signals to enhance debugging.
Understand the best way to sinchronize clocks of sender and receiver for correct delay measurement."""

#global variables
end_loop = False
init_time = 0

# Create a TCP/IP socket
serversocket = socket.socket(socket.AF_INET, # Internet
                             socket.SOCK_STREAM) # TCP/IP

serveraddress = ('localhost', 30001) #(IP,PORT)
serversocket.bind(serveraddress)
serversocket.listen(5)
print("Waiting for TCP/IP connection setup...")
(clientsocket, address) = serversocket.accept()
print('Setting up on {} port {}'.format(*serveraddress))
time.sleep(3) 
print('Begin communication...}')
init_time=time.time()

#1° idea: replicate packing/unpacking of 'byte pack' from Simulink®
def pack_vector(X):
    b = bytes()
    b = b.join((struct.pack('>d', val) for val in X))
    return b

async def TCP_IP_send(msg):
    clientsocket.send(msg)

#2° idea: use serialized formats e.g. json

init_time=time.time()

async def main():
    for x in range(50):
        data = [time.time()-init_time,x]
        await TCP_IP_send(pack_vector(data))
        time.sleep(0.01)

    print('Stop communication.}')
asyncio.run(main())


    
