# -*- coding: utf-8 -*-

import logging
import asyncio
import platform
import ast
import struct
import sys

from bleak import BleakClient
from bleak import BleakScanner

from datetime import datetime

# These values have been randomly generated - they must match between the Central and Peripheral devices
# Any changes you make here must be suitably made in the Arduino program as well

TEMP_UUID = '19b10000-2001-537e-4f6c-d104768a1214'

arduino_board_name = 'NiclaSenseME-6743' #insert here your personal board's name

end_loop = False

async def scan_devices():

    print('Arduino Nicla Sense ME Central Service')
    print('Looking for Arduino Nicla Sense ME Peripheral Device...')

    device = None
    devices = await BleakScanner.discover()
    for d in devices:       
        if 'NiclaSenseME-6743' in d.name:
            print('Found Arduino Nicla Sense ME Peripheral')
            found = True
            async with BleakClient(d.address) as client:
                print(f'Connected to {d.address}')
                
    if not found:
        print('Could not find Nicla Sense ME Peripheral')

def main():
    while not end_loop:
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(scan_devices())
        except KeyboardInterrupt:
            print('\nReceived Keyboard Interrupt')
            loop.close()
            sys.exit(0)
        finally:
            loop.close()

if __name__ == "__main__":
    main()
        
