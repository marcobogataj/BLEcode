import asyncio
from datetime import datetime
from bleak import BleakClient, BleakScanner
import struct
from helper_functions import ble_sense_uuid, setup_logging
from pynput import keyboard
import sys

# Constants
KNOWN_ADDRESSES = [
    # "DD:FC:F2:76:67:43",
    "39FD4BD4-7DDA-4BE3-82F9-F969E569A119"
]
TIMEOUT = 10

SENSOR_NAME_LIST = [
    "service ID",
    "temperature",
]
ID_LIST = [
    "0000",  # service ID, not to be read
    "2001",  # temperature
]

CHARACTERISTIC_NAMES_TO_UUIDS = {
    charac_name: ble_sense_uuid(charac_id)
    for charac_name, charac_id in zip(SENSOR_NAME_LIST, ID_LIST)
}
CHARACTERISTIC_UUIDS_TO_NAMES = {
    charac_uuid: charac_name
    for charac_name, charac_uuid in CHARACTERISTIC_NAMES_TO_UUIDS.items()
}

# global variables
sensor_read = {charac_name: None for charac_name in SENSOR_NAME_LIST[1:]}
stop_notification = False
notification_toggle_needed = True
unpair_client = False
end_loop = False

# Setup global logging
name = "root"
now = datetime.now()
datetime_str = now.strftime("%Y_%m_%d_%H_%M_%S")
filepath_log = fr"/Users/marcobogataj/Documents/UNI/magistrale/BG/Industrial IoT/Nicla Sense ME/BLEcode/python/log/nicla_{datetime_str}.log"

print(filepath_log)

log_root = setup_logging(name, filepath_log)

# Setup files - Don't really like the position of this one
# File path - Might want to change this so that each file is created when a nicla is connected and reattached if connection is lost TODO
filepath_out = fr"/Users/marcobogataj/Documents/UNI/magistrale/BG/Industrial IoT/Nicla Sense ME/BLEcode/python/data/nicla_{datetime_str}.dat"


async def connection_and_notification(client):
    log_root.info("Connecting to device...")
    try:
        await client.connect()
    except Exception as e:
        log_root.error(f"Exception: {e}")
        log_root.error("Connection failed!")
        return

    global unpair_client
    unpair_client = False

    try:
        log_root.info("Requesting notification on sensors...")
        await start_notifications(client)
        await listen_for_notifications(client)
    except Exception as e:
        log_root.error(f"Exception: {e}")
        log_root.error("Notification request failed!")
        log_root.error("Force disconnection...")
        await client.disconnect()


async def start_notifications(client):
    for sensor_name in SENSOR_NAME_LIST[1:]:
        await client.start_notify(
            CHARACTERISTIC_NAMES_TO_UUIDS[sensor_name], update_sensor_read
        )

    global notification_toggle_needed
    notification_toggle_needed = False
    log_root.info("The central will be notified from now on...")


async def stop_notifications(client):
    for sensor_name in SENSOR_NAME_LIST[1:]:
        await client.stop_notify(CHARACTERISTIC_NAMES_TO_UUIDS[sensor_name])

    global notification_toggle_needed
    notification_toggle_needed = False
    log_root.info("The central will not be notified anymore...")


async def listen_for_notifications(client):
    global stop_notification, notification_toggle_needed
    stop_notification = False

    # setting up the hotkey to stop notifications
    listener = keyboard.GlobalHotKeys(
        {
            "<ctrl>+<alt>+n": toggle_notifications_handler,
            "<ctrl>+<alt>+p": unpair_handler,
        }
    )
    listener.start()
    while client.is_connected and not unpair_client:
        if not stop_notification:
            if notification_toggle_needed:
                await start_notifications(client)
            log_root.info(
                "Listening for notification... (<ctrl>+<alt>+n to toggle notifications, <ctrl>+<alt>+p to unpair)"
            )
            await asyncio.sleep(1)
        else:
            if notification_toggle_needed:
                await stop_notifications(client)
            log_root.info(
                "Not listening... (<ctrl>+<alt>+n to toggle notifications, <ctrl>+<alt>+p to unpair)"
            )
            await asyncio.sleep(1)

    listener.stop()
    await client.disconnect()


def toggle_notifications_handler():
    global stop_notification, notification_toggle_needed
    if stop_notification:
        log_root.info("Forcefully starting notifications (<ctrl>+<alt>+n)!")
    else:
        log_root.info("Forcefully stopping notifications (<ctrl>+<alt>+n)!")

    stop_notification = not stop_notification
    notification_toggle_needed = True


def unpair_handler():
    log_root.info("Forcefully unpairing device (<ctrl>+<alt>+p)!")
    global unpair_client
    unpair_client = True


async def scan_devices():
    device = None
    while device is None:
        log_root.info("Wait...")
        await asyncio.sleep(1)
        log_root.info("Searching for devices...")
        device = await BleakScanner.find_device_by_filter(
            match_known_addresses, timeout=TIMEOUT
        )

    log_root.info(f"Device found: {device.address}")
    client = BleakClient(device, disconnected_callback=on_disconnection)
    await connection_and_notification(client)
    return 0


def on_disconnection(device):
    if unpair_client:
        log_root.info(f"Device {device.address} unpaired successfully!")
        log_root.info(f"Do you still want to scan for new devices? (y/n)")
        res = str.lower(input())
        if res != "y":
            global end_loop
            end_loop = True
    else:
        log_root.info(f"Lost connection with {device.address}")


def match_known_addresses(device, advertisement_data):
    return device.address in KNOWN_ADDRESSES


async def update_sensor_read(sender, data):
    sensor_name = CHARACTERISTIC_UUIDS_TO_NAMES[sender.uuid]
    log_root.info(f"Notification received from {sensor_name} sensor")

    global sensor_read
    if sensor_read[sensor_name] is not None:
        log_root.info(f"Sensor {sensor_name} was already read!")

    sensor_read[sensor_name] = data

    if all(sensor_read[x] is not None for x in sensor_read.keys()):
        log_root.info("All sensor read, proceed to log...")
        log_sensors()
        clear_sensors()


def log_sensors():
    global sensor_read
    now = datetime.now()
    temperature = struct.unpack("f", sensor_read["temperature"])[0]

    str_to_write = f"{str(now)},{str(temperature)}\n"
    log_root.info(f"Packet received: {str_to_write[:-2]}")

    # TODO

    with open(filepath_out, "a") as fp:
        fp.write(str_to_write)

    log_root.info("Data written!")


def clear_sensors():
    global sensor_read
    for k in sensor_read.keys():
        sensor_read[k] = None


def main():
    # Header
    with open(filepath_out, "w") as fp:
        fp.write("datetime,temperature\n")

    while not end_loop:
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(scan_devices())
        except KeyboardInterrupt:
            log_root.info("Exiting on keyboard interrupt!")
            loop.close()
            sys.exit(0)
        except Exception as e:
            log_root.error("Something happened, restarting scan...")
        finally:
            loop.close()


if __name__ == "__main__":
    main()
