import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import random 
from functools import partial

import socket
import struct

# Create a UDP socket
sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_STREAM) # TCP/IP

# Bind the socket to the port
UDP_IP = '0.0.0.0'
UDP_PORT = 2
server_address = (UDP_IP, UDP_PORT)
print('starting up on {} port {}'.format(*server_address))
sock.bind(server_address)

def animate(i,dL):
    global k                             
    data, address = sock.recvfrom(512) #Receive UDP data
    output = struct.unpack('d',data)
    #print("received message:", output) 
    print(i)                                            # 'i' is a incrementing variable based upon frames = x argument
    dL.append(output)                                   # Add to the list holding the fixed number of points to animate
    ax.clear()                                          # Clear last data frame
    ax.plot(dL)                                         # Plot new data frame

    if i==0:
        k = 0
    if i%100==0 and i!=0:
        k += 1
        print('Slide')

    ax.set_ylim([-10, 10])                                # Set Y axis limit of plot
    ax.set_xlim(left = k*100, right=k*100+100)   
    ax.set_title("Simulink data")                       # Set title of figure
    ax.set_ylabel("Value")                              # Set title of y axis
    ax.grid(True)
                              
dataList = []                                           # Create empty list variable for later use                                                                                    
fig = plt.figure()                                      # Create Matplotlib plots fig is the 'higher level' plot window
ax = fig.add_subplot(111)                               # Add subplot to main fig window

ani = animation.FuncAnimation(fig, partial(animate, dL=dataList), frames=10000, interval=30)

plt.show()                                              # Keep Matplotlib plot persistent on screen until it is closed



