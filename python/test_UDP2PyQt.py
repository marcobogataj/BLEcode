# Import libraries
from numpy import *
from pyqtgraph.Qt import QtWidgets, QtCore
import pyqtgraph as pg

import socket
import struct

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 

# Bind the socket to the port
UDP_IP = '0.0.0.0'
UDP_PORT = 2
server_address = (UDP_IP, UDP_PORT)
print('starting up on {} port {}'.format(*server_address))
sock.bind(server_address)

### START QtApp #####
app = QtWidgets.QApplication([])            # you MUST do this once (initialize things)
####################

win = pg.GraphicsLayoutWidget(title="Signal from serial port") # creates a window
p = win.addPlot(title="Realtime plot")                         # creates empty space for the plot in the window
curve = p.plot()                                               # create an empty "plot" (a curve to plot)

windowWidth = 500                       # width of the window displaying the curve
Xm = linspace(0,0,windowWidth)          # create array that will contain the relevant time series     
ptr = -windowWidth                      # set first x position
win.show()

# Realtime data plot. Each time this function is called, the data display is updated
def update():
    global curve, ptr, Xm    
    Xm[:-1] = Xm[1:]                          # shift data in the temporal mean 1 sample left
    data, address = sock.recvfrom(512)        # Receive UDP data
    value = struct.unpack('d',data)                
    Xm[-1] = double(value)                    # vector containing the instantaneous values      
    ptr += 1                                  # update x position for displaying the curve
    curve.setData(Xm)                         # set the curve with this data
    curve.setPos(ptr,0)                       # set x position in the graph to 0
    QtWidgets.QApplication.processEvents()    # you MUST process the plot now

### MAIN PROGRAM #####    
# this is a brutal infinite loop calling your realtime data plot
while True: update()

### END QtApp ####
pg.QtWidgets.QApplication.exec_() # you MUST put this at the end
##################