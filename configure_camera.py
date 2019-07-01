#!/usr/bin/env python3
import os


def configure_camera(cam_no):
	with open("commandlog.txt", "r") as log:
	    cmd = log.readline().strip('\n')
	    while cmd:
	        # print(cmd)
	        mod_com = "prometheus-cli/build/prom-cli -a \"{}\" -i {} | hexdump".format(cmd, cam_no)
	        #print(mod_com)
	        os.system(mod_com)
	        cmd = log.readline().strip('\n')
	        if (cmd == "getBWSorted"):
	            break
	#print("build/prom-cli -a \"getBWSorted\" -i 0 > image.bin")
