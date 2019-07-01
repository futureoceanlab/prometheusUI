
#face buttons
MENU_BTN = 10
DISP_BTN = 9
EXPO_BTN = 0
ACTN_BTN = 11
HDR_BTN = 0

#js1
JS1_MENU_BTN = 14
JS1_DISP_BTN = 15
JS1_EXPO_BTN = 18
JS1_ACTN_BTN = 23
JS1_HDR_BTN = 24

#js2
JS2_MENU_BTN = 5
JS2_DISP_BTN = 6
JS2_EXPO_BTN = 13
JS2_ACTN_BTN = 19
JS2_HDR_BTN = 26

#BBB
BBB_0_ctrl = 12
BBB_1_ctrl =20
BBB_0_reset = 16
BBB_1_reset = 21

#i2c
I2C_DATA = 2		#never explicitly called
I2C_CLOCK = 3		#never explicitly called

#misc
LED_CAM_SELECT = 7
SHUTTER_OUTPUT = 25 #called only from C files
LED_ENABLE = 8


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

def js1_menuGPIO():
	return JS1_MENU_BTN

def js1_dispGPIO():
	return JS1_DISP_BTN

def js1_expoGPIO():
	return JS1_EXPO_BTN

def js1_actnGPIO():
	return JS1_ACTN_BTN

def js1_hdrGPIO():
	return JS1_HDR_BTN

def js2_menuGPIO():
	return JS2_MENU_BTN

def js2_dispGPIO():
	return JS2_DISP_BTN

def js2_expoGPIO():
	return JS2_EXPO_BTN

def js2_actnGPIO():
	return JS2_ACTN_BTN

def js2_hdrGPIO():
	return JS2_HDR_BTN

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

def led_enable_GPIO():
	return LED_ENABLE