#include <DHT.h>
//
// =======================
//  Sensor Pins
// =======================
//
#define VOLTAGE_SENSOR 32   // ZMPT101B
#define CURRENT_SENSOR 25   // ACS712
#define DHT_PIN        23    // DHT11

#define DHTTYPE DHT11
DHT dht(DHT_PIN, DHTTYPE);

//
// =======================
//  Calibration Constants
// =======================
//
const float VOLTAGE_SCALE = 250.0;       // Adjust for ZMPT101B
const float CURRENT_SENSITIVITY = 0.185; // ACS712 5A module
const float ZERO_OFFSET = 1.65;          // Midpoint of ADC (1.65V)

//
// =======================
//  RMS Voltage Function
// =======================
//
float readVoltageRMS(int samples = 300) {
  double sum = 0;
  for (int i = 0; i < samples; i++) {
    int adc = analogRead(VOLTAGE_SENSOR);
    float v = (adc * 3.3 / 4095.0) - ZERO_OFFSET;
    sum += v * v;
    delayMicroseconds(250);
  }
  return sqrt(sum / samples) * VOLTAGE_SCALE;
}

//
// =======================
//  RMS Current Function
// =======================
//
float readCurrentRMS(int samples = 300) {
  double sum = 0;
  for (int i = 0; i < samples; i++) {
    int adc = analogRead(CURRENT_SENSOR);
    float v = (adc * 3.3 / 4095.0) - ZERO_OFFSET;
    sum += v * v;
    delayMicroseconds(250);
  }
  return sqrt(sum / samples) / CURRENT_SENSITIVITY;
}

//
// =======================
//      SETUP
// =======================
//
void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  dht.begin();
  delay(1000);

  Serial.println("ESP32 Sensor Test Started...");
}

//
// =======================
//      LOOP
// =======================
//
void loop() {

  float voltage = readVoltageRMS();
  float current = readCurrentRMS();

  float temperature = dht.readTemperature();
  if (isnan(temperature)) temperature = 0; // fallback

  // Print in CSV Format
  Serial.print(voltage, 2);
  Serial.print(",");
  Serial.print(current, 2);
  Serial.print(",");
  Serial.println(temperature, 2);

  delay(1000);
}
