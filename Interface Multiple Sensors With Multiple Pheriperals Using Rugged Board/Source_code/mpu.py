import mraa
import time

# MPU6050 I2C address
MPU6050_ADDR = 0x68
MPU6050_ADDR_ALT = 0x69

# MPU6050 Registers
PWR_MGMT_1 = 0x6B
ACCEL_XOUT_H = 0x3B
GYRO_XOUT_H = 0x43
WHO_AM_I = 0x75

# Initialize I2C object
i2c = mraa.I2c(0)  # Use I2C bus 1 (ensure it's correct for your board)
i2c.address(MPU6050_ADDR)

def initialize_mpu6050():
    # Try reading the WHO_AM_I register
    who_am_i = i2c.readReg(WHO_AM_I)
    if who_am_i != 0x68:
        i2c.address(MPU6050_ADDR_ALT)
        who_am_i = i2c.readReg(WHO_AM_I)
        if who_am_i != 0x69:
            print("Error: Device not found or wrong address. WHO_AM_I = {}".format(who_am_i))
            exit(1)

    # Wake up the MPU6050 (clear sleep bit)
    i2c.writeReg(PWR_MGMT_1, 0x00)
    time.sleep(0.1)  # Add a small delay after waking up the device
    print("MPU6050 initialized.")

def read_word(register):                   
    try:                                                           
        # Read two bytes from the register and combine them        
        high = i2c.readReg(register)                       
        low = i2c.readReg(register + 1)                    
        value = (high << 8) + low                          
        # Handle signed values                             
        if value >= 0x8000:                                                                  
            value = -((65535 - value) + 1)                                                   
        return value                                                                         
    except ValueError:                     
        print("Error reading register {}".format(register))
        return 0                                                   
                                                                   
def get_sensor_data():                                             
    # Read accelerometer and gyroscope data                
    accel_x = read_word(ACCEL_XOUT_H)                           
    accel_y = read_word(ACCEL_XOUT_H + 2)                       
    accel_z = read_word(ACCEL_XOUT_H + 4)                                                    
                                                                                             
    gyro_x = read_word(GYRO_XOUT_H)                                                          
    gyro_y = read_word(GYRO_XOUT_H + 2)                                                      
    gyro_z = read_word(GYRO_XOUT_H + 4)    
                                                                   
    return (accel_x, accel_y, accel_z), (gyro_x, gyro_y, gyro_z)                         
                                                                                         
if __name__ == "__main__":                                                               
    initialize_mpu6050()                                                                 
                                                                                 
    try:                                                                                     
        while True:                                             
            accel, gyro = get_sensor_data()                        
            print("Accelerometer: X={}, Y={}, Z={}".format(accel[0], accel[1], accel[2]))
            print("Gyroscope: X={}, Y={}, Z={}".format(gyro[0], gyro[1], gyro[2]))       
            time.sleep(1)                                                                
    except KeyboardInterrupt:                                                            
        print("Exiting...") 

