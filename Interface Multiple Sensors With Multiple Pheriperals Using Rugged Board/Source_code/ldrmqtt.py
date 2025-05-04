import time
import os
import paho.mqtt.client as mqtt

# MQTT Configuration
MQTT_BROKER = "167.179.83.158"  # Replace with your broker address
MQTT_PORT = 1884  # Default MQTT port
MQTT_TOPIC = "8G9fwPHLsj1yjNUX0LaY"  # Topic to publish LDR data

# Auto-detect ADC device
ADC_DEVICE_PATH = "/sys/bus/iio/devices/"
adc_device = None

# Find the ADC device dynamically
for device in os.listdir(ADC_DEVICE_PATH):
    if device.startswith("iio:device"):
        adc_device = "{}{}/in_voltage6_raw".format(ADC_DEVICE_PATH, device)
        break

if not adc_device:
    print("Error: ADC device not found!")
    exit(1)

# ADC Configuration
VREF = 3.3  # Reference voltage
ADC_RESOLUTION = 4096  # 12-bit ADC

# Light intensity thresholds
DARK_THRESHOLD = 3000  # High ADC value -> Dark
LIGHT_THRESHOLD = 500   # Low ADC value -> Bright

def read_adc():
    """Reads the LDR sensor value from the ADC."""
    try:
        with open(adc_device, "r") as file:
            raw_value = int(file.read().strip())
        return raw_value
    except Exception as e:
        print("Error reading ADC: {}".format(e))
        return None

# MQTT Setup
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT Broker with result code {}".format(rc))

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

try:
    print("Starting LDR Sensor Monitoring with MQTT...")

    while True:
        ldr_value = read_adc()
        if ldr_value is not None:
            voltage = (ldr_value / ADC_RESOLUTION) * VREF
            
            # Determine light condition
            if ldr_value > DARK_THRESHOLD:
                status = "Sunlight Not Available (Dark)"
            elif ldr_value < LIGHT_THRESHOLD:
                status = "Sunlight Available (Bright)"
            else:
                status = "Transitional Light Condition"
            
            # Create payload
            payload = "{{'ldr_value': {}, 'voltage': {:.2f}, 'status': '{}'}}".format(ldr_value, voltage, status)
            
            # Publish to MQTT
            mqtt_client.publish(MQTT_TOPIC, payload)
            print("Published: {}".format(payload))
        
        time.sleep(1)  # Read every second

except KeyboardInterrupt:
    print("\nExiting Program")
    mqtt_client.loop_stop()
    mqtt_client.disconnect()

