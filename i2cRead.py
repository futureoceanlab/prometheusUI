import Adafruit_PureIO.smbus as smbus

# address = 0x18
# reg_temp = 0x00
i2c_ch = 1
bus = smbus.SMBus(i2c_ch)


import time
# import smbus

i2c_ch = 1

# TMP102 address on the I2C bus
i2c_address = 0x18

# Register addresses
reg_temp = 0x00
reg_config = 0x01


# Read temperature registers and calculate Celsius
def read_temp():

    # Read temperature registers
    val = bus.readS16BE(i2c_address)
    print("a ", val)
    val = ((val << 8) & 0xFF00) + (val >> 8)
    print("b ", val)
# Print out temperature every second
while True:
    temperature = read_temp()
    print(temperature, "C")
    time.sleep(1)