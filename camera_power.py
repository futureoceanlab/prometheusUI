#!/usr/bin/env python3

from gpiozero import LED, Button
import os
import sys
import time

def turn_on_BBBx(x):
    # control pin for BBB0
    bbb0_ctrl = LED(7)
    bbb1_ctrl = LED(8)
    # sys_reset polling pins
    reset0 = Button(25)
    reset1 = Button(24)
    print("start power cycle %d!" %(x))
    if (x == 0):
        power_cycle(x, bbb0_ctrl, reset0)
    else:
        power_cycle(x, bbb1_ctrl, reset1)
    return


def power_cycle(target, bbb_ctrl, bbb_reset):
    pwr_success = False 
    cnt = 1
    print(bbb_reset.value)
    ######## While loop until success
    while (not pwr_success):
        print("power cycle attemp %d..." %(cnt))
        # in case on, turn it off first
        if (bbb_reset.value == 0):
            if (prom_cli_works(target)):
                print("it was already on and functional,")
                # prom cli was successful, we are done
                return
            print("Board is already on but not functional, so shutting down...")
            bbb_ctrl.on()
            # Wait until reset goes down
            bbb_reset.wait_for_press()
            bbb_ctrl.off()
        print("Board is off now, turn on start...")
        # power is off, turn it on
        bbb_ctrl.on()
        print("wait for reset to come up")
        # wait until reset goes up
        bbb_reset.wait_for_release()
        # power is on
        bbb_ctrl.off()
        print("The baord is up!, wait 20 seconds...")
        # delay 20 seconds, check prom-cli
        time.sleep(20)
        # check the first four digits are 0000
        if (prom_cli_works(target)):
            pwr_success = True
        cnt+=1
    return

# Check if prom cli returns successfully
def prom_cli_works(target):
    outcome_name = "redirect.txt"
    cwd = os.getcwd()
    prom_cli = os.path.join(cwd, "prometheus-cli", "build", "prom-cli")
    prom_cli += " -a \"setSpeedOfLight 300000000.\" -i %d | hexdump >> %s" %(target, outcome_name)
    print(prom_cli)
    #original = sys.stdout
    with open(outcome_name, 'a+') as outcome:
        #sys.stdout = outcome
        os.system(prom_cli)
        #sys.stdout = original
        firstSix = outcome.read(6)
    os.remove(outcome_name)
    if firstSix == "000000":
        print("prom cli check is successful")
        return True
    else:
        print("prom cli check failed...!")
        return False

if __name__ == "__main__":
#    prom_cli_works()
    target = sys.argv[1]
    print("Start power cycling BBB target %s" %(target))
    if (target == '0'):
        turn_on_BBBx(0)
    elif (target == '1'):
        turn_on_BBBx(1)
    else:
        turn_on_BBBx(0)
        turn_on_BBBx(1)
