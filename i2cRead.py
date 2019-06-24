import smbus

address = 0x18
reg_temp = 0x00
i2c_ch = 1
bus = smbus.SMBus(i2c_ch)

def read_temp():
	print('testinnnnggg')
	value = bus.read_i2c_block_data(address, reg_temp, 2)
	return

if __name__ =='__main__':
	read_temp()
