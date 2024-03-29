#include "Nicla_System.h"
#include "Arduino_BHY2.h"
#include <ArduinoBLE.h>
#include <Streaming.h>

#define BLE_SENSE_UUID(val) ("19b10000-" val "-537e-4f6c-d104768a1214")
#define ACQUISITION_INTERVAL 10
#define SCAN_INTERVAL 1000

// Constants
const int VERSION = 0x00000000;

// BLE variables
BLEService service(BLE_SENSE_UUID("0000"));

BLEUnsignedIntCharacteristic versionCharacteristic(BLE_SENSE_UUID("1001"), BLERead | BLENotify);
BLEFloatCharacteristic timeCharacteristic(BLE_SENSE_UUID("2001"), BLERead | BLENotify);

BLECharacteristic rgbLedCharacteristic(BLE_SENSE_UUID("8001"), BLERead | BLEWrite, 3 * sizeof(byte));  // Array of 3 bytes, RGB

// String for the local and device name
String name;

// variable to be to check for time to be passed
unsigned long last_acq_time;
unsigned long last_scan_time;

// To take care of central
bool central_discovered;
BLEDevice central;

void setup() {
  Serial.begin(115200);

  //Serial.println("Start");

  nicla::begin();
  nicla::leds.begin();
  nicla::leds.setColor(red);

  //Sensors initialization
    BHY2.begin(NICLA_STANDALONE);
    
  if (!BLE.begin()) {
    //Serial.println("Failed to initialize BLE!");
    while (1)
      ;
  }

  String address = BLE.address();

  //Serial.print("address = ");
  //Serial.println(address);

  address.toUpperCase();

  name = "NiclaSenseME-";
  name += address[address.length() - 5];
  name += address[address.length() - 4];
  name += address[address.length() - 2];
  name += address[address.length() - 1];

  //Serial.print("name = ");
  //Serial.println(name);

  BLE.setLocalName(name.c_str());
  BLE.setDeviceName(name.c_str());
  BLE.setAdvertisedService(service);

  // Add all the previously defined Characteristics
  service.addCharacteristic(versionCharacteristic);
  service.addCharacteristic(timeCharacteristic);
  service.addCharacteristic(rgbLedCharacteristic);

  rgbLedCharacteristic.setEventHandler(BLEWritten, onRgbLedCharacteristicWrite);
  versionCharacteristic.setValue(VERSION);

  BLE.addService(service);
  BLE.advertise();

  central_discovered = false;
  BLEDevice central;

  last_scan_time = 0;
  last_acq_time = 0;
}

void loop() 
{
  if (!central_discovered) 
  {
    if (millis() - last_scan_time > SCAN_INTERVAL) 
    {
      last_scan_time = millis();

      // Scan every SCAN_INTERVAL ms
      // Search for a central
      nicla::leds.setColor(yellow);
      central = BLE.central();
      //Serial.println("Scanning for central device...");

      if (central)
      {
        central_discovered = true;
        //Serial.print("Central device found and connected! Device MAC address: ");
        //Serial.println(central.address());
      }

    } 
    else nicla::leds.setColor(red);

  }
  else 
  {
    if (millis() - last_acq_time > ACQUISITION_INTERVAL)
     {
      if (central) 
      {
        if (central.connected()) 
        {
          last_acq_time = millis();
          nicla::leds.setColor(blue);
          BHY2.update();
          unsigned long time = millis();

          Serial << time << endl;;
          if (timeCharacteristic.subscribed())
          {
          timeCharacteristic.writeValue(time); 
          }       
        }

      }
      else 
      {
        central_discovered = false;
      }
    } 
    else 
    {
      nicla::leds.setColor(green);
      if (!central.connected()) 
      {     
        central_discovered = false;        
      } 
    }  
  }
}

void check_subscriptions() 
{
  if (timeCharacteristic.subscribed()) 
  {
    time_notify();              
  }
}

void time_notify()
{
  float time = millis();
  timeCharacteristic.writeValue(time);
}

void onRgbLedCharacteristicWrite(BLEDevice central, BLECharacteristic characteristic)
{
  byte r = rgbLedCharacteristic[0];
  byte g = rgbLedCharacteristic[1];
  byte b = rgbLedCharacteristic[2];

  nicla::leds.setColor(r, g, b);
}
