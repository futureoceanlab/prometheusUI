import time

import Adafruit_MCP9808.MCP9808 as MCP9808

sensor = MCP9808.MCP9808()

# Optionally you can override the address and/or bus number:
#sensor = MCP9808.MCP9808(address=0x20, busnum=2)

# Initialize communication with the sensor.
sensor.begin()

temp = sensor.readTempC()



while True:
	temp = sensor.readTempC()
	print(temp)
	time.sleep(1)