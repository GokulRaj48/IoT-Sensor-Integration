import time
import mraa

# Define GPIO Pins
TRIG_PIN = 12
ECHO_PIN = 13

# Initialize MRAA
mraa.init()

# Setup GPIO
trigPin = mraa.Gpio(TRIG_PIN)
echoPin = mraa.Gpio(ECHO_PIN)

trigPin.dir(mraa.DIR_OUT)
echoPin.dir(mraa.DIR_IN)

def measure_distance():
    # Send Trigger Pulse
    trigPin.write(0)
    time.sleep(0.00001)  # 10�µs delay

    trigPin.write(1)
    time.sleep(0.00001)  # 10�µs pulse
    trigPin.write(0)

    # Wait for Echo to go HIGH (start time)
    start_time = time.time()
    timeout = start_time + 0.02  # 20ms timeout
    while echoPin.read() == 0:
        start_time = time.time()
        if start_time > timeout:
            print("Echo signal timeout (no response)")
            return None  # No valid measurement

    # Wait for Echo to go LOW (stop time)
    stop_time = time.time()
    timeout = stop_time + 0.02  # 20ms timeout
    while echoPin.read() == 1:
        stop_time = time.time()
        if stop_time > timeout:
            print("Echo signal timeout (stuck HIGH)")
            return None  # No valid measurement

    # Calculate time difference
    elapsed_time = stop_time - start_time
    distance = (elapsed_time * 34300) / 2  # Speed of sound in cm/s

    return distance

try:
    while True:
        distance = measure_distance()
        if distance is not None:
            print("Distance: %.2f cm" % distance)  # Python 2 & 3 compatible print
        else:
            print("Measurement failed, check connections")

        time.sleep(0.3)  # 300ms delay

except KeyboardInterrupt:
    print("\nMeasurement stopped")

