import socket
import struct
import matplotlib as m
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.animation as animation
from matplotlib import style

style.use('fivethirtyeight')

fig = plt.figure()
plt.axis([0,10,0,1])
plt.ion()

samples = 500
channels = np.linspace(start= 0, stop = 0,num = samples)

def animate(channels):
    plt.plot(range(0,samples),channels)
    plt.draw()
    plt.pause(0.2)

def shift_left(lst):
    try:
        return lst[1:] + [lst[0]]
    except IndexError:
        return lst

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
    data, address = sock.recvfrom(512)   
    output = struct.unpack('d',data)
    msgcount +=1
    # write output to channel
    channels=shift_left(channels)
    channels[samples-1]=output
    animate(channels)
