#!/usr/bin/env python3
"""
The idea of the code to reconfigure is the following:
There is an existing joystick pin dictionary look up table as a json file.
For each gpio pins that could be used as a button gpio, we register a callback function.
The call back function will set a value for each keyword (i.e. button)
and save it into a new json file (new_joystick_pin.json). 

In UI.py Application.__init__(), we can read the json file to configure the buttons
with the newly set pins. 
"""
from gpiozero import Button
import json

import prom_GPIO as pg


original_btn_json_file = "original_joystick_pin.json"
new_btn_json_file = "new_joystick_pin.json"
btn_json_path = os.path.join(os.getcwd(), original_btn_json_file)
new_btn_json_path = os.path.join(os.getcwd(), new_btn_json_file)
new_btn_dict = {}

BTN1 = gpio.Button(pg.menuGPIO())
BTN2 = gpio.Button(pg.dispGPIO())
BTN3 = gpio.Button(pg.actnGPIO())
BTN4 = gpio.Button(pg.js1_menuGPIO())
BTN5 = gpio.Button(pg.js1_dispGPIO())
BTN6 = gpio.Button(pg.js1_expoGPIO())
BTN7 = gpio.Button(pg.js1_actnGPIO())
BTN8 = gpio.Button(pg.js1_hdrGPIO())
BTN9 = gpio.Button(pg.js2_menuGPIO())
BTN10 = gpio.Button(pg.js2_dispGPIO())
BTN11 = gpio.Button(pg.js2_expoGPIO())
BTN12 = gpio.Button(pg.js2_actnGPIO())
BTN13 = gpio.Button(pg.js2_hdrGPIO())
gpio_btns = [BTN1, BTN2, BTN3, BTN4, BTN5, BTN6, BTN7, BTN8, BTN9, BTN10, BTN11, BTN12, BTN13]
cur_btn = None
btn_is_set = False

def set_joystick_pin(button):
    # set the value of btn to this pin in the lookup table
    print("Changed {} to pin {}".format(cur_btn, button.pin))
    new_btn_dict[cur_btn] = button.pin
    btn_is_set = True


if __name__ == "__main__":
    # Set up gpio buttons to callback
    for gpio_btn in gpio_btns:
        gpio_btn.when_pressed = set_joystick_pin
    # Open the original dict 
    with open(btn_json_path, 'r') as orig_json:
        btn_dict = json.load(orig_json) 
        print("Please press the button that corresponds to the following button:\n")
        for btn_key, _ in btn_dict:
            print(btn_key)
            cur_btn = btn_key
            # Wait until any set_joystick_pin is called
            while not btn_is_set:
                continue
            btn_is_set = False
    with open(new_btn_json_path, 'a') as new_json:
        json.dumps(new_btn_dict, new_json, indent=4, sort_keys=True)
    print("Complete. Please check the new_joystick_pin.json")
