import time
import os

# Paths
ADC_BASE_PATH = "/sys/bus/iio/devices/"

# Auto-detect ADC device (Ensure we select the correct one)
adc_device = None
scale_path = None

for device in os.listdir(ADC_BASE_PATH):
    name_path = os.path.join(ADC_BASE_PATH, device, "name")
    if os.path.exists(name_path):
        with open(name_path, "r") as f:
            name = f.read().strip()
        if "adc" in name.lower():  # Ensure it's the ADC, not MPU-6050
            adc_device = os.path.join(ADC_BASE_PATH, device, "in_voltage6_raw")
            scale_path = os.path.join(ADC_BASE_PATH, device, "in_voltage_scale")
            break

if not adc_device:
    print("Error: ADC device not found!")
    exit(1)

# Read ADC scale (Voltage scaling factor)
VREF = 3.3  # Default reference voltage
if scale_path and os.path.exists(scale_path):
    with open(scale_path, "r") as f:
        VREF = float(f.read().strip())  # Read ADC scale dynamically

# ADC resolution (Usually 12-bit -> 4096 levels, but can vary)
ADC_RESOLUTION = 4096  

# Light intensity thresholds (modify based on calibration)
DARK_THRESHOLD = 3000   # High ADC value -> Dark
LIGHT_THRESHOLD = 500   # Low ADC value -> Bright

def read_adc():
    """Reads the LDR sensor value from the ADC."""
    try:
        with open(adc_device, "r") as file:
            raw_value = int(file.read().strip())  # Read ADC value
        return raw_value
    except Exception as e:
        print("Error reading ADC: {}".format(e))  
        return None

try:
    print("Starting LDR Sensor Monitoring...")

    while True:
        ldr_value = read_adc()  # Read ADC value
        if ldr_value is not None:
            voltage = (ldr_value / ADC_RESOLUTION) * VREF  # Convert to voltage
            
            # Determine light condition
            if ldr_value > DARK_THRESHOLD:
                status = "Sunlight Not Available (Dark)"
            elif ldr_value < LIGHT_THRESHOLD:
                status = "Sunlight Available (Bright)"
            else:
                status = "Transitional Light Condition"

            print("LDR Value: {}, Voltage: {:.2f}V -> {}".format(ldr_value, voltage, status))  

        time.sleep(1)  # Read every second

except KeyboardInterrupt:
    print("\nExiting Program")

