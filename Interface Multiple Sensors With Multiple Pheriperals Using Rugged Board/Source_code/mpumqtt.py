import mraa
import time
import paho.mqtt.client as mqtt  # MQTT Library

# MQTT Configuration
BROKER = "167.179.83.158"  # Use your broker address
PORT = 1884
TOPIC = "8G9fwPHLsj1yjNUX0LaY"

# MPU6050 I2C address
MPU6050_ADDR = 0x68
MPU6050_ADDR_ALT = 0x69

# MPU6050 Registers
PWR_MGMT_1 = 0x6B
ACCEL_XOUT_H = 0x3B
GYRO_XOUT_H = 0x43
WHO_AM_I = 0x75

# Initialize I2C object
i2c = mraa.I2c(0)  # Ensure the correct I2C bus is used
i2c.address(MPU6050_ADDR)

def initialize_mpu6050():
    """ Initialize the MPU6050 sensor """
    try:
        who_am_i = i2c.readReg(WHO_AM_I)
        if who_am_i != 0x68:
            i2c.address(MPU6050_ADDR_ALT)
            who_am_i = i2c.readReg(WHO_AM_I)
            if who_am_i != 0x69:
                print("Error: MPU6050 not detected, WHO_AM_I = {}".format(who_am_i))
                return False

        i2c.writeReg(PWR_MGMT_1, 0x00)  # Wake up the MPU6050
        time.sleep(0.1)
        print("MPU6050 initialized successfully.")
        return True

    except Exception as e:
        print("MPU6050 initialization failed: {}".format(e))
        return False

def read_word(register):
    """ Read a word (2 bytes) from the I2C register """
    try:
        high = i2c.readReg(register)
        low = i2c.readReg(register + 1)
        value = (high << 8) + low

        if value >= 0x8000:  # Convert to signed value
            value = -((65535 - value) + 1)

        return value
    except Exception as e:
        print("Error reading register {}: {}".format(register, e))
        return 0

def get_sensor_data():
    """ Read accelerometer and gyroscope data """
    accel_x = read_word(ACCEL_XOUT_H)
    accel_y = read_word(ACCEL_XOUT_H + 2)
    accel_z = read_word(ACCEL_XOUT_H + 4)

    gyro_x = read_word(GYRO_XOUT_H)
    gyro_y = read_word(GYRO_XOUT_H + 2)
    gyro_z = read_word(GYRO_XOUT_H + 4)

    return (accel_x, accel_y, accel_z), (gyro_x, gyro_y, gyro_z)

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    """ Handle MQTT connection status """
    if rc == 0:
        print("Connected to MQTT Broker")
    else:
        print("Failed to connect, return code {}".format(rc))

def on_publish(client, userdata, mid):
    """ Handle successful message publish """
    print("Data Published to MQTT Broker")

# MQTT Client Setup
client = mqtt.Client()
client.on_connect = on_connect
client.on_publish = on_publish
client.connect(BROKER, PORT, 60)  # Connect to MQTT broker
client.loop_start()  # Start the MQTT loop

if __name__ == "__main__":
    if initialize_mpu6050():
        try:
            while True:
                accel, gyro = get_sensor_data()

                # Create JSON payload
                payload = '{{"accel_x": {}, "accel_y": {}, "accel_z": {}, "gyro_x": {}, "gyro_y": {}, "gyro_z": {}}}'.format(
                    accel[0], accel[1], accel[2], gyro[0], gyro[1], gyro[2]
                )

                print("Publishing: " + payload)
                client.publish(TOPIC, payload)  # Publish to MQTT

                time.sleep(2)  # Publish every 2 seconds

        except KeyboardInterrupt:
            print("Exiting...")
            client.loop_stop()  # Stop MQTT loop
            client.disconnect()  # Disconnect MQTT client

