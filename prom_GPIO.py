
#face buttons
MENU_BTN = 21
DISP_BTN = 20
EXPO_BTN = 16
ACTN_BTN = 12
HDR_BTN = 0000000

#BBB
BBB_0_ctrl = 7
BBB_1_ctrl = 8
BBB_0_reset = 23
BBB_1_reset = 24

#i2c
I2C_DATA = 2		#never explicitly called
I2C_CLOCK = 3		#never explicitly called

#misc
LED_CAM_SELECT = 18
SHUTTER_OUTPUT = 21 #called only from C files
MOD_CLOCK = 4		#called only from C files
LED_ENABLE = 0000000


#getter functions
def menuGPIO():
	return MENU_BTN

def dispGPIO():
	return DISP_BTN

def expoGPIO():
	return EXPO_BTN

def actnGPIO():
	return ACTN_BTN

def hdrGPIO():
	return HDR_BTN

def bbb0_ctrl_GPIO():
	return BBB_0_ctrl

def bbb1_ctrl_GPIO():
	return BBB_1_ctrl

def bbb0_reset_GPIO():
	return BBB_0_reset

def bbb1_reset_GPIO():
	return BBB_1_reset

def i2c_data_GPIO():
	return I2C_DATA

def i2c_clock_GPIO():
	return I2C_CLOCK

def led_cam_select_GPIO():
	return LED_CAM_SELECT

def shutter_output_GPIO():
	return SHUTTER_OUTPUT

def mod_clock_GPIO():
	return MOD_CLOCK

def led_enable_GPIO():
	return LED_ENABLE