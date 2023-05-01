import asyncio
from bleak import BleakScanner, BleakClient

KNOWN_ADDRESSES = "DD:FC:F2:76:67:43"
address = "39FD4BD4-7DDA-4BE3-82F9-F969E569A119"
uuid_temperature_characteristic = "19b10000-2001-537e-4f6c-d104768a1214"

async def scan_devices():
    devices = await BleakScanner.discover()
    for d in devices:
        if d.name == 'NiclaSenseME-6743':
            myDevice = d 
            print('Found it')
 
            print(f"Device found: {d.address}")
            print(d.details)

asyncio.run(scan_devices())