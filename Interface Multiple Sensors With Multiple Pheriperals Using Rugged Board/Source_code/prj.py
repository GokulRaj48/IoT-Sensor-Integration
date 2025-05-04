import time
import os
import threading
import mraa

# === MPU6050 Configuration ===
MPU6050_ADDR = 0x68
PWR_MGMT_1 = 0x6B
ACCEL_XOUT_H = 0x3B
GYRO_XOUT_H = 0x43
WHO_AM_I = 0x75

i2c = mraa.I2c(0)
i2c.address(MPU6050_ADDR)

def initialize_mpu6050():
    who_am_i = i2c.readReg(WHO_AM_I)
    if who_am_i != 0x68:
        print("Error: MPU6050 not found. WHO_AM_I = {}".format(who_am_i))
        exit(1)
    i2c.writeReg(PWR_MGMT_1, 0x00)
    time.sleep(0.1)
    print("MPU6050 initialized.")

def read_word(register):
    try:
        high = i2c.readReg(register)
        low = i2c.readReg(register + 1)
        value = (high << 8) + low
        if value >= 0x8000:
            value = -((65535 - value) + 1)
        return value
    except ValueError:
        print("Error reading register {}".format(register))
        return 0

def get_sensor_data():
    accel_x = read_word(ACCEL_XOUT_H)
    accel_y = read_word(ACCEL_XOUT_H + 2)
    accel_z = read_word(ACCEL_XOUT_H + 4)
    gyro_x = read_word(GYRO_XOUT_H)
    gyro_y = read_word(GYRO_XOUT_H + 2)
    gyro_z = read_word(GYRO_XOUT_H + 4)
    return (accel_x, accel_y, accel_z), (gyro_x, gyro_y, gyro_z)

def mpu6050_task():
    initialize_mpu6050()
    while running:
        accel, gyro = get_sensor_data()
        print("\n�🔹 MPU6050 - Accelerometer: X={}, Y={}, Z={}".format(accel[0], accel[1], accel[2]))
        print("�🔹 MPU6050 - Gyroscope: X={}, Y={}, Z={}".format(gyro[0], gyro[1], gyro[2]))
        time.sleep(1)

# === LDR Sensor Configuration ===
ADC_BASE_PATH = "/sys/bus/iio/devices/"
adc_device = None
scale_path = None

for device in os.listdir(ADC_BASE_PATH):
    name_path = os.path.join(ADC_BASE_PATH, device, "name")
    if os.path.exists(name_path):
        with open(name_path, "r") as f:
            name = f.read().strip()
        if "adc" in name.lower():
            adc_device = os.path.join(ADC_BASE_PATH, device, "in_voltage6_raw")
            scale_path = os.path.join(ADC_BASE_PATH, device, "in_voltage_scale")
            break

if not adc_device:
    print("Error: ADC device not found!")
    exit(1)

VREF = 3.3
if scale_path and os.path.exists(scale_path):
    with open(scale_path, "r") as f:
        VREF = float(f.read().strip())

ADC_RESOLUTION = 4096
DARK_THRESHOLD = 3000
LIGHT_THRESHOLD = 500

def read_adc():
    try:
        with open(adc_device, "r") as file:
            raw_value = int(file.read().strip())
        return raw_value
    except Exception as e:
        print("Error reading ADC: {}".format(e))
        return None

def ldr_sensor_task():
    while running:
        ldr_value = read_adc()
        if ldr_value is not None:
            voltage = (ldr_value / ADC_RESOLUTION) * VREF
            if ldr_value > DARK_THRESHOLD:
                status = "�🔸 Sunlight Not Available (Dark)"
            elif ldr_value < LIGHT_THRESHOLD:
                status = "�🔸 Sunlight Available (Bright)"
            else:
                status = "�🔸 Transitional Light Condition"
            print("\n�🔸 LDR Value: {}, Voltage: {:.2f}V -> {}".format(ldr_value, voltage, status))
        time.sleep(1)

# === Ultrasonic Sensor Configuration ===
TRIG_PIN = 12
ECHO_PIN = 13
mraa.init()
trigPin = mraa.Gpio(TRIG_PIN)
echoPin = mraa.Gpio(ECHO_PIN)
trigPin.dir(mraa.DIR_OUT)
echoPin.dir(mraa.DIR_IN)

def measure_distance():
    trigPin.write(0)
    time.sleep(0.00001)
    trigPin.write(1)
    time.sleep(0.00001)
    trigPin.write(0)
    
    start_time = time.time()
    timeout = start_time + 0.02
    while echoPin.read() == 0:
        start_time = time.time()
        if start_time > timeout:
            print("�🔺 Echo signal timeout (no response)")
            return None
    
    stop_time = time.time()
    timeout = stop_time + 0.02
    while echoPin.read() == 1:
        stop_time = time.time()
        if stop_time > timeout:
            print("�🔺 Echo signal timeout (stuck HIGH)")
            return None
    
    elapsed_time = stop_time - start_time
    distance = (elapsed_time * 34300) / 2
    return distance

def ultrasonic_task():
    while running:
        distance = measure_distance()
        if distance is not None:
            print("\n�🔺 Distance: %.2f cm" % distance)
        else:
            print("�🔺 Measurement failed, check connections")
        time.sleep(1)

# === Running All Sensors Simultaneously in Order ===
if __name__ == "__main__":
    running = True  # Flag to control all threads

    # Create sensor threads
    thread_mpu = threading.Thread(target=mpu6050_task)
    thread_ldr = threading.Thread(target=ldr_sensor_task)
    thread_ultrasonic = threading.Thread(target=ultrasonic_task)

    # Start sensor threads
    thread_mpu.start()
    time.sleep(2)  # Delay before starting LDR sensor
    thread_ldr.start()
    time.sleep(2)  # Delay before starting Ultrasonic sensor
    thread_ultrasonic.start()

    try:
        # Keep running until user presses Ctrl+C
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n Stopping all sensors... Please wait.")
        running = False  # Stop all threads gracefully

        # Wait for all threads to finish
        thread_mpu.join()
        thread_ldr.join()
        thread_ultrasonic.join()
        
        print(" All sensors stopped. Exiting Program.")

