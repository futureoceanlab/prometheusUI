import smbus

address = 0x18
reg_temp = 0x00
i2c_ch = 1
bus = smbus.SMBus(i2c_ch)

def twos_comp(val, bits):
    if (val & (1 << (bits - 1))) != 0:
        val = val - (1 << bits)
    return val

# Read temperature registers and calculate Celsius
def read_temp():

    # Read temperature registers
    val = bus.read_i2c_block_data(address, reg_temp, 3)
    temp_c = (val[0] << 4) | (val[1] >> 5)
    print("val: ", val)
    print("temp_c: ", temp_c)

    # Convert to 2s complement (temperatures can be negative)
    temp_c = twos_comp(temp_c, 12)
    print("twos: ", temp_c)

    # Convert registers value to temperature (C)
    temp_c = temp_c * 0.0625
    print(temp_c)

    return temp_c


if __name__ =='__main__':
	while True:
		read_temp()
