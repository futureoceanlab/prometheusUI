import time
import logging
import math
import board
import busio
import adafruit_si5351


# Default I2C address for device.
MCP9808_I2CADDR_DEFAULT        = 0x3c

# Register addresses.
MCP9808_REG_CONFIG             = 0x01
MCP9808_REG_UPPER_TEMP         = 0x02
MCP9808_REG_LOWER_TEMP         = 0x03
MCP9808_REG_CRIT_TEMP          = 0x04
MCP9808_REG_AMBIENT_TEMP       = 0x05
MCP9808_REG_MANUF_ID           = 0x06
MCP9808_REG_DEVICE_ID          = 0x07


class MCP9808(object):
	"""Class to represent an Adafruit MCP9808 precision temperature measurement
	board.
	"""

	def __init__(self, address=MCP9808_I2CADDR_DEFAULT, i2c=None, **kwargs):
		"""Initialize MCP9808 device on the specified I2C address and bus number.
		Address defaults to 0x18 and bus number defaults to the appropriate bus
		for the hardware.
		"""
		self._logger = logging.getLogger('Adafruit_MCP9808.MCP9808')
		if i2c is None:
			import Adafruit_GPIO.I2C as I2C
			i2c = I2C
		self._device = i2c.get_i2c_device(address, **kwargs)


	def begin(self):
		"""Start taking temperature measurements. Returns True if the device is 
		intialized, False otherwise.
		"""
		# Check manufacturer and device ID match expected values.
		mid = self._device.readU16BE(MCP9808_REG_MANUF_ID)
		did = self._device.readU16BE(MCP9808_REG_DEVICE_ID)
		self._logger.debug('Read manufacturer ID: {0:04X}'.format(mid))
		self._logger.debug('Read device ID: {0:04X}'.format(did))
		return mid == 0x0054 and did == 0x0400

	def readTempC(self):
		"""Read sensor and return its value in degrees celsius."""
		# Read temperature register value.
		t = self._device.readU16BE(MCP9808_REG_AMBIENT_TEMP)
		self._logger.debug('Raw ambient temp register value: 0x{0:04X}'.format(t & 0xFFFF))
		# Scale and convert to signed value.
		temp = (t & 0x0FFF) / 16.0
		if t & 0x1000:
			temp -= 256.0
		return temp



def getTemperature():
	sensor = MCP9808()
	sensor.begin()
	return sensor.readTempC()

def writeClock(freq_mult, divisor):
	i2c = busio.I2C(board.SCL, board.SDA)
 
	# Initialize SI5351.
	si5351 = adafruit_si5351.SI5351(i2c)

	si5351.pll_a.configure_integer(freq_mult) 
	print('PLL A frequency: {0}mhz'.format(si5351.pll_a.frequency/1000000))
	 
	
	# si5351.pll_b.configure_fractional(24, 2, 3)  # Multiply 25mhz by 24.667 (24 2/3)
	# print('PLL B frequency: {0}mhz'.format(si5351.pll_b.frequency/1000000))
	 
	
	si5351.clock_0.configure_integer(si5351.pll_a, divisor)
	print('Clock 0: {0}mhz'.format(si5351.clock_0.frequency/1000000))
	 

	# si5351.clock_1.configure_fractional(si5351.pll_b, 45, 1, 2) # Divide by 45.5 (45 1/2)
	# print('Clock 1: {0}mhz'.format(si5351.clock_1.frequency/1000000))
	 
	
	# si5351.clock_2.configure_integer(si5351.pll_b, 900)

	# si5351.clock_2.r_divider = adafruit_si5351.R_DIV_64
	# print('Clock 2: {0}khz'.format(si5351.clock_2.frequency/1000))
	 
	# After configuring PLLs and clocks, enable the outputs.
	si5351.outputs_enabled = True
	# You can disable them by setting false.


