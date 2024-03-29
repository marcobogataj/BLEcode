#include "Nicla_System.h"
#include "Arduino_BHY2.h"
#include <ArduinoBLE.h>

#define BLE_SENSE_UUID(val) ("19b10000-" val "-537e-4f6c-d104768a1214")
#define SLOW_ACQUISITION_INTERVAL 5000
#define FAST_ACQUISITION_INTERVAL 100
#define SCAN_INTERVAL 1000

// Constants
const int VERSION = 0x00000000;
const float conv = 16/pow(2,16);

// BLE variables
BLEService service(BLE_SENSE_UUID("0000"));

BLEUnsignedIntCharacteristic versionCharacteristic(BLE_SENSE_UUID("1001"), BLERead | BLENotify);
BLEFloatCharacteristic temperatureCharacteristic(BLE_SENSE_UUID("2001"), BLERead | BLENotify);
BLEUnsignedIntCharacteristic humidityCharacteristic(BLE_SENSE_UUID("3001"), BLERead | BLENotify);
BLEFloatCharacteristic pressureCharacteristic(BLE_SENSE_UUID("4001"),  BLERead | BLENotify);

BLECharacteristic accelerometerCharacteristic(BLE_SENSE_UUID("5001"), BLERead | BLENotify, 3 * sizeof(float));  // Array of 3x 2 Bytes, XYZ (float) g
BLECharacteristic gyroscopeCharacteristic(BLE_SENSE_UUID("6001"), BLERead | BLENotify, 3 * sizeof(float));    // Array of 3x 2 Bytes, XYZ (float) dps
BLECharacteristic quaternionCharacteristic(BLE_SENSE_UUID("7001"), BLERead | BLENotify, 4 * sizeof(float));     // Array of 4x 2 Bytes, XYZW (float) uT

BLECharacteristic rgbLedCharacteristic(BLE_SENSE_UUID("8001"), BLERead | BLEWrite, 3 * sizeof(byte));  // Array of 3 bytes, RGB

BLEFloatCharacteristic bsecCharacteristic(BLE_SENSE_UUID("9001"), BLERead | BLENotify);
BLEIntCharacteristic  co2Characteristic(BLE_SENSE_UUID("9002"), BLERead | BLENotify);
BLEUnsignedIntCharacteristic gasCharacteristic(BLE_SENSE_UUID("9003"), BLERead | BLENotify);

// String for the local and device name
String name;

// Sensor declarations
Sensor temperature(SENSOR_ID_TEMP);
Sensor humidity(SENSOR_ID_HUM);
Sensor pressure(SENSOR_ID_BARO);
Sensor gas(SENSOR_ID_GAS);
SensorXYZ gyroscope(SENSOR_ID_GYRO);
SensorXYZ accelerometer(SENSOR_ID_ACC);
SensorQuaternion quaternion(SENSOR_ID_RV);
SensorBSEC bsec(SENSOR_ID_BSEC);

// variable to be to check for time to be passed
unsigned long last_slow_acq_time;
unsigned long last_fast_acq_time;
unsigned long last_scan_time;

// To take care of central
bool central_discovered;
BLEDevice central;

void setup() {
  Serial.begin(115200);

  Serial.println("Start");

  nicla::begin();
  nicla::leds.begin();
  nicla::leds.setColor(red);

  //Sensors initialization
    BHY2.begin(NICLA_STANDALONE);
    temperature.begin();
    humidity.begin();
    pressure.begin();
    gyroscope.begin();
    accelerometer.begin();
    quaternion.begin();
    bsec.begin();
    gas.begin();

  if (!BLE.begin()) {
    Serial.println("Failed to initialize BLE!");
    while (1)
      ;
  }

  String address = BLE.address();

  Serial.print("address = ");
  Serial.println(address);

  address.toUpperCase();

  name = "NiclaSenseME-";
  name += address[address.length() - 5];
  name += address[address.length() - 4];
  name += address[address.length() - 2];
  name += address[address.length() - 1];

  Serial.print("name = ");
  Serial.println(name);

  BLE.setLocalName(name.c_str());
  BLE.setDeviceName(name.c_str());
  BLE.setAdvertisedService(service);

  // Add all the previously defined Characteristics
  service.addCharacteristic(versionCharacteristic);
  service.addCharacteristic(temperatureCharacteristic);
  service.addCharacteristic(humidityCharacteristic);
  service.addCharacteristic(pressureCharacteristic);
  service.addCharacteristic(versionCharacteristic);
  service.addCharacteristic(accelerometerCharacteristic);
  service.addCharacteristic(gyroscopeCharacteristic);
  service.addCharacteristic(quaternionCharacteristic);
  service.addCharacteristic(bsecCharacteristic);
  service.addCharacteristic(co2Characteristic);
  service.addCharacteristic(gasCharacteristic);
  service.addCharacteristic(rgbLedCharacteristic);

  rgbLedCharacteristic.setEventHandler(BLEWritten, onRgbLedCharacteristicWrite);
  versionCharacteristic.setValue(VERSION);

  BLE.addService(service);
  BLE.advertise();

  central_discovered = false;
  BLEDevice central;

  last_scan_time = 0;
  last_fast_acq_time = 0;
  last_slow_acq_time = 0;
}

void loop() {
  if (!central_discovered) {
    if (millis() - last_scan_time > SCAN_INTERVAL) {
      last_scan_time = millis();

      // Scan every SCAN_INTERVAL ms
      // Search for a central
      nicla::leds.setColor(yellow);
      central = BLE.central();
      Serial.println("Scanning for central device...");

      if (central) {
        central_discovered = true;
        Serial.print("Central device found and connected! Device MAC address: ");
        Serial.println(central.address());
      }

    } else nicla::leds.setColor(red);

  } else {
    if (millis() - last_fast_acq_time > FAST_ACQUISITION_INTERVAL) {
      if (central) {
        if (central.connected()) {
          last_fast_acq_time = millis();
          nicla::leds.setColor(blue);
          BHY2.update();
          //Check only fast sampling sensors like accelerometer and gyroscope
          check_subscriptions(0);

          if (millis() - last_slow_acq_time > SLOW_ACQUISITION_INTERVAL) {
            last_slow_acq_time = millis();
            //Check also slow sensors such as temperature, humidity, iaq & co2
            check_subscriptions(1);
          }
        }
      } else {
        central_discovered = false;
        // TODO
      }
    } else {
      nicla::leds.setColor(green);

      if (!central.connected()) {     
        central_discovered = false;        
      } 
    }
  }
}

void check_subscriptions(int mode) {

  if (accelerometerCharacteristic.subscribed()) {
    accelerometer_notify();              
  }
  if (gyroscopeCharacteristic.subscribed()) {
    gyroscope_notify();              
  }

  if (mode==1){
    if (temperatureCharacteristic.subscribed()) {
      temperature_notify();              
    }
    if (humidityCharacteristic.subscribed()) {
      humidity_notify();              
    }
    if (pressureCharacteristic.subscribed()) {
      pressure_notify();              
    }
    if (bsecCharacteristic.subscribed()) {
    bsec_notify();              
    }
    if (co2Characteristic.subscribed()) {
      co2_notify();              
    }
    if (gasCharacteristic.subscribed()) {
      gas_notify();              
    }
  }
}

void accelerometer_notify() {
  float x, y, z;
  x = accelerometer.x()*conv;
  y = accelerometer.y()*conv;
  z = accelerometer.z()*conv;

  float accelerometerValues[] = {x, y, z};
  accelerometerCharacteristic.writeValue(accelerometerValues, sizeof(accelerometerValues));
}

void gyroscope_notify() {
  float x, y, z;

  x = gyroscope.x()*conv;;
  y = gyroscope.y()*conv;;
  z = gyroscope.z()*conv;;

  float gyroscopeValues[3] = {x, y, z};

  gyroscopeCharacteristic.writeValue(gyroscopeValues, sizeof(gyroscopeValues));
}

void temperature_notify(){
  float temperatureValue = temperature.value();
  temperatureCharacteristic.writeValue(temperatureValue);
}

void humidity_notify(){
  uint8_t humidityValue = humidity.value() + 0.5f;  //since we are truncating the float type to a uint8_t, we want to round it
  humidityCharacteristic.writeValue(humidityValue);
}

void pressure_notify(){
  float pressureValue = pressure.value();
  pressureCharacteristic.writeValue(pressureValue);
}

void bsec_notify(){
  float airQuality = float(bsec.iaq());
  bsecCharacteristic.writeValue(airQuality);
}

void co2_notify(){
  uint32_t co2 = bsec.co2_eq();
  co2Characteristic.writeValue(co2);
}

void gas_notify(){
  unsigned int g = gas.value();
  gasCharacteristic.writeValue(g);
}

void onRgbLedCharacteristicWrite(BLEDevice central, BLECharacteristic characteristic){
  byte r = rgbLedCharacteristic[0];
  byte g = rgbLedCharacteristic[1];
  byte b = rgbLedCharacteristic[2];

  nicla::leds.setColor(r, g, b);
}
