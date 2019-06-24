#!/usr/bin/env python3
import os
with open("commandlog.txt", "r") as log:
    cmd = log.readline().strip('\n')
    while cmd:
        # print(cmd)
        mod_com = "build/prom-cli -a \"{}\" -i 0 | hexdump".format(cmd)
        print(mod_com)
        os.system(mod_com)
        cmd = log.readline().strip('\n')
        if (cmd == "getBWSorted"):
            break
print("build/prom-cli -a \"getBWSorted\" -i 0 >> image.bin")