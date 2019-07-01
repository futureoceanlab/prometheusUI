#!/usr/bin/env python3

from gpiozero import LED, Button
#from timeout import timeout
import os
import sys
import time
import signal
import shlex, subprocess
import prom_GPIO as pg

def connect_both_cameras():
    # control pin for BBB0
    bbb0_ctrl = LED(pg.bbb0_ctrl_GPIO())
    bbb1_ctrl = LED(pg.bbb1_ctrl_GPIO())
    # sys_reset polling pins
    reset0 = Button(pg.bbb0_reset_GPIO())
    reset1 = Button(pg.bbb1_reset_GPIO())
    bbb0_works = False
    bbb1_works = False
    # if a board is on, check the prom cli!
    if (reset0.value == 0):
        bbb0_works = prom_cli_check(0)
    if (reset1.value == 0):
        bbb1_works = prom_cli_check(1)

    # when both are not prom-cling, make sure that the
    # bbb0 turns on first!
    while (not bbb0_works or  not bbb1_works):
        while not bbb0_works:
            print("BBB0 prom_cli not working: Turn off BBB0")
            turn_off(bbb0_ctrl, reset0)
            if (not bbb1_works):
                print("BBB1 prom_cli not work: oh, cameras need to be re-ordered")
                turn_off(bbb1_ctrl, reset1)
            turn_on(bbb0_ctrl, reset0)
            bbb0_works = prom_cli_check(0)
        print("BBB0 is working!")
        # bbb0 (192.168.8.2) is connected, turn on bbb1
        while not bbb1_works:
            print("BUT! BBB1 is not working")
            turn_off(bbb1_ctrl, reset1)
            turn_on(bbb1_ctrl, reset1)
            bbb1_works = prom_cli_check(1)
        print("BBB1 is now working")
        bbb0_works = prom_cli_check(0)
        bbb1_works = prom_cli_check(1)

    print("Both cameras are working!")


def turn_off(bbb_ctrl, bbb_reset):
    if (bbb_reset.value == 0):
        print("Board is on so shutting down...")
        bbb_ctrl.on()
        # Wait until reset goes down
        bbb_reset.wait_for_press()
        bbb_ctrl.off()
    else:
        print("Board is off already")
        return


def turn_on(bbb_ctrl, bbb_reset):
    # is bbb on already?
    if (bbb_reset.value == 0):
        print("Board is already on!")
        return
    else:
        print("Board is off now, turn on start...")
        # power is off, turn it on
        bbb_ctrl.on()
        print("wait for reset to come up")
        # wait until reset goes up
        bbb_reset.wait_for_release()
        # power is on
        bbb_ctrl.off()
        print("The baord is up!, wait 30 seconds...")
        # delay 20 seconds, check prom-cli
        time.sleep(30)
        # check the first four digits are 0000


# Check if prom cli returns successfully
#@timeout
def prom_cli_check(target):
    outcome_name = "redirect.txt"
    cwd = os.getcwd()
    prom_cli = os.path.join(cwd, "prometheus-cli", "build", "prom-cli")
    prom_cli += " -a \"setSpeedOfLight 300000000.\" -i %d | hexdump" %(target)
    args = shlex.split(prom_cli)
    #print(args)
    original = sys.stdout
    firstSix = "FAILED"
    with open(outcome_name, 'a+') as outcome:
        #sys.stdout = outcome
    #   try:
    #       with timeout(seconds=5):
    # Set time out to 10 seconds
        t = 5
        p = subprocess.Popen(args=prom_cli, shell=True, stdout=outcome)
        try:
            p.wait(timeout=t)
            #print(outs)
            #print(firstSix)
            #if firstSix == "000000":
            #    print("prom cli check is successful")
            #    return True
            #sys.stdout = original
        except subprocess.TimeoutExpired:
            p.kill()
        #    sys.stdout = original
            print("prom cli timedout...!")
            #return False
        #finally:
            #print(firstSix)
    # # os.system(prom_cli)
    # firstSix = outcome.read(6)
    # #   except TimeoutError as e:
    # #       print(e)
    #     #sys.stdout = original
    #os.remove(outcome_name)
    with open(outcome_name, 'r') as out:
        firstSix = out.read(6) 
        print("Result: " + firstSix)
    os.remove(outcome_name)
    if firstSix == "000000":
         print("prom cli check is successful")
         return True
    else:
         print("prom cli check failed...!")
         return False

# class timeout:
#     def __init__(self, seconds=1, error_message="Timeout"):
#         self.seconds = seconds
#         self.error_message = error_message

#     def handle_timeout(self, signum, frame):
#         raise TimeoutError(self.error_message)

#     def __enter__(self):
#         signal.signal(signal.SIGALRM, self.handle_timeout)
#         signal.alarm(self.seconds)

#     def __exit__(self, type, value, traceback):
#         signal.alarm(0)


if __name__ == "__main__":
    #try:
    #    with timeout(seconds=3):
    #        time.sleep(4)
    #except TimeoutError as e:
    #    print("Got here?")
    #prom_cli_works()
    connect_both_cameras()

#    target = sys.argv[1]
#    print("Start power cycling BBB target %s" %(target))
#    if (target == '0'):
#        turn_on_BBBx(0)
#    elif (target == '1'):
#        turn_on_BBBx(1)
#    else:
#        turn_on_BBBx(0)
#        turn_on_BBBx(1)
