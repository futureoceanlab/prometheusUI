import os
from gpiozero import LED
import readBinary as binReader
import prom_GPIO as pg
import subprocess

def capturePhotoCommand2D(filename):
    # Sanity power check may be required 
    # setup API
    cwd = os.getcwd()
    prom_cli = os.path.join(cwd, "prometheus-cli", "build", "prom-cli")
    cmd = " -a \"getBWSorted\"" 
    file0 = filename + "_0.bin"
    file1 = filename + "_1.bin"
    prom_cli0 = prom_cli + cmd + " -i 0  > %s" %(file0)
    prom_cli1 = prom_cli + cmd + " -i 1  > %s" %(file1)
    camsel = LED(pg.led_cam_select_GPIO())
    # capture 0 

    print("COMMAND : ", prom_cli0)
    camsel.off()
    subprocess_command(prom_cli0, error_msg="2D getBWsorted from BBB0 failed")
    # capture 1
    camsel.on()
    subprocess_command(prom_cli1, error_msg="2D getBWsorted from BBB1 failed")
    # os.system(prom_cli1)
    camsel.off()
    # image processing
    # img0s = binReader.readBinaryFile(file0)
    # img1s = binReader.readBinaryFile(file1)
    return [file0, file1]

def capturePhotoCommand3D(filename):
    # sanity check may be necessary
    # setup API
    cwd = os.getcwd()
    prom_cli = os.path.join(cwd, "prometheus-cli", "build", "prom-cli")
    cmd = " -a \"getDCSSorted\"" 
    file0 = filename + "_0.bin"
    file1 = filename + "_1.bin"
    prom_cli0 = prom_cli + cmd + " -i 0 > %s" %(file0)
    prom_cli1 = prom_cli + cmd + " -i 1 > %s" %(file1)
    camsel = LED(pg.led_cam_select_GPIO())
    # capture 0 
    camsel.off()
    # os.system(prom_cli0)
    subprocess_command(prom_cli0, error_msg="3D getDSCsorted from BBB0 failed")
    # capture 1
    camsel.on()
    # os.system(prom_cli1)
    subprocess_command(prom_cli1, error_msg="3D getDSCsorted from BBB1 failed")
    camsel.off()

    # image processing
    # img0s = binReader.readBinaryFile(file0)
    # img1s = binReader.readBinaryFile(file1)
    return [file0, file1]

def change2dExposure(exposure):
    # Power sanity might be neede
    exp_options = [30, 100, 300, 1000, 3000]
    if (exposure in exp_options):
        cwd = os.getcwd()
        prom_cli = os.path.join(cwd, "prometheus-cli", "build", "prom-cli")
        cmd = " -a \"setIntegrationTime2D %d.\"" %(exposure) 
        prom_cli0 = prom_cli + cmd + " -i 0 | hexdump"
        prom_cli1 = prom_cli + cmd + " -i 1 | hexdump"
        # Timer may be required
        subprocess_command(prom_cli0, error_msg="BBB0 2D exposure change failed")
        subprocess_command(prom_cli1, error_msg="BBB1 2D exposure change failed")
    else:
        print("Invalid 2D exposure value")


def change3dExposure(exposure):
    # -sanity check of power may be required
    exp_options = [30, 100, 300, 1000, 3000]
    if (exposure in exp_options):
        cwd = os.getcwd()
        prom_cli = os.path.join(cwd, "prometheus-cli", "build", "prom-cli")
        cmd = " -a \"setIntegrationTime3D %d.\"" %(exposure) 
        prom_cli0 = prom_cli + cmd + " -i 0 | hexdump"
        prom_cli1 = prom_cli + cmd + " -i 1 | hexdump"
        # Timer may be required
        subprocess_command(prom_cli0, error_msg="BBB0 3D exposure change failed")
        subprocess_command(prom_cli1, error_msg="BBB1 3D exposure change failed")
    else:
        print("Invalid 3D exposure value")


def toggle2d3dMode(mode):
    # -sanity check of power may be required
    if (mode == 0 or mode == 1):
        cwd = os.getcwd()
        prom_cli = os.path.join(cwd, "prometheus-cli", "build", "prom-cli")
        cmd = " -a \"setEnableImaging 0.\""
        cmd2 = " -a \"loadConfig %d.\"" %(mode)
        prom_cli0 = prom_cli + cmd + " -i 0 | hexdump"
        prom_cli1 = prom_cli + cmd + " -i 1 | hexdump"
        prom_cli0_2 = prom_cli + cmd + " -i 0 | hexdump"
        prom_cli1_2 = prom_cli + cmd + " -i 1 | hexdump"
        # Timer may be required
        subprocess_command(prom_cli0, error_msg="BBB0 2D 3D toggle failed")
        subprocess_command(prom_cli1, error_msg="BBB1 2D 3D toggle failed")
        subprocess_command(prom_cli0_2, error_msg="BBB0 2D 3D load config failed")
        subprocess_command(prom_cli1_2, error_msg="BBB1 2D 3D load config failed")
    else:
        print("Invalid input for toggling 2D and 3D")



def setModulationFrequency(freq):
    # -sanity check of power may be required
    if (freq == 0 or freq == 1):
        cwd = os.getcwd()
        prom_cli = os.path.join(cwd, "prometheus-cli", "build", "prom-cli")
        cmd = " -a \"setModulationFrequency %d.\"" %(freq)
        prom_cli0 = prom_cli + cmd + " -i 0 | hexdump"
        prom_cli1 = prom_cli + cmd + " -i 1 | hexdump"
        # Timer may be required
        subprocess_command(prom_cli0, error_msg="BBB0 mod freq change failed")
        subprocess_command(prom_cli1, error_msg="BBB1 mod freq change failed")
    else:
        print("modulation frequency invalid input")



def enablePiDelay(enable):
    # -sanity check of power may be required
    if (enable == 0):
        cwd = os.getcwd()
        prom_cli = os.path.join(cwd, "prometheus-cli", "build", "prom-cli")
        cmd = " -a \"enablePiDelay %d.\"" %(enable)
        prom_cli0 = prom_cli + cmd + " -i 0 | hexdump"
        prom_cli1 = prom_cli + cmd + " -i 1 | hexdump"
        # Timer may be required
        subprocess_command(prom_cli0, error_msg="BBB0 enable PiDelay failed")
        subprocess_command(prom_cli1, error_msg="BBB1 enable PiDelay failed")
    else:
        print("Invalid input to enable pi delay")


def enableCapture(enable):
    # -sanity check of power may be required
    if (enable == 0):
        cwd = os.getcwd()
        prom_cli = os.path.join(cwd, "prometheus-cli", "build", "prom-cli")
        cmd = " -a \"setEnableImaging %d.\"" %(enable)
        prom_cli0 = prom_cli + cmd + " -i 0 | hexdump"
        prom_cli1 = prom_cli + cmd + " -i 1 | hexdump"
        # Timer may be required
        subprocess_command(prom_cli0, error_msg="BBB0 enable capture failed")
        subprocess_command(prom_cli1, error_msg="BBB1 enable capture failed")
    else:
        print("Invalid input to enable imaging")

def changeClockSource(source):
    # -sanity check of power may be required
    if (source == 0 or source==1):
        if source:
            #external clock
            clock_value = '7f'
        else:
            #internal clock
            clock_value = '3f'
        cwd = os.getcwd()
        prom_cli = os.path.join(cwd, "prometheus-cli", "build", "prom-cli")
        cmd = " -a \"write 80 "+clock_value+".\"" 
        prom_cli0 = prom_cli + cmd + " -i 0 | hexdump"
        prom_cli1 = prom_cli + cmd + " -i 1 | hexdump"
        # Timer may be required
        subprocess_command(prom_cli0, error_msg="BBB0 change clock cycle failed")
        subprocess_command(prom_cli1, error_msg="BBB1 change clock cycle failed")
    else:
        print("Invalid input to enable imaging")


def subprocess_command(cmd, error_msg):
    with  open('redirect.txt', 'a+') as outcome: 
        p = subprocess.Popen(args=cmd, shell=True, stdout=outcome)
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            p.kill()
            print(error_msg)