import os
from gpiozero import LED

def capturePhotoCommand2D(filename):
    # Sanity power check may be required 
    # setup API
    cwd = os.getcwd()
    prom_cli = os.path.join(cwd, "prometheus-cli", "build", "prom-cli")
    cmd = " -a \"getBWSorted\"" 
    file0 = filename + "_0.bin"
    file1 = filename + "_1.bin"
    prom_cli0 = prom_cli + cmd + " -i 0 | hexdump >> %s" %(file0)
    prom_cli1 = prom_cli + cmd + " -i 1 | hexdump >> %s" %(file1)
    camsel = LED(18)
    # capture 0 
    camsel.off()
    os.system(prom_cli0)
    # capture 1
    camsel.on()
    os.system(prom_cli1)

    # image processing

def capturePhotoCommand3D(filename):
    # sanity check may be necessary
    # setup API
    cwd = os.getcwd()
    prom_cli = os.path.join(cwd, "prometheus-cli", "build", "prom-cli")
    cmd = " -a \"getDCSSorted\"" 
    file0 = filename + "_0.bin"
    file1 = filename + "_1.bin"
    prom_cli0 = prom_cli + cmd + " -i 0 | hexdump >> %s" %(file0)
    prom_cli1 = prom_cli + cmd + " -i 1 | hexdump >> %s" %(file1)
    camsel = LED(18)
    # capture 0 
    camsel.off()
    os.system(prom_cli0)
    # capture 1
    camsel.on()
    os.system(prom_cli1)

    # image processing

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
        os.system(prom_cli0)
        os.system(prom_cli1)
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
        os.system(prom_cli0)
        os.system(prom_cli1)
    else:
        print("Invalid 3D exposure value")


def toggle2d3dMode(mode):
    # -sanity check of power may be required
    if (mode == 0 or mode == 1):
        cwd = os.getcwd()
        prom_cli = os.path.join(cwd, "prometheus-cli", "build", "prom-cli")
        cmd = " -a \"setEnableImaging %d.\"" %(mode) 
        prom_cli0 = prom_cli + cmd + " -i 0 | hexdump"
        prom_cli1 = prom_cli + cmd + " -i 1 | hexdump"
        # Timer may be required
        os.system(prom_cli0)
        os.system(prom_cli1)
    else:
        print("Invalid input for toggling 2D and 3D")



def setModulationFrequency(freq):
    # -sanity check of power may be required
    if (enable == 0 or enable == 1):
        cwd = os.getcwd()
        prom_cli = os.path.join(cwd, "prometheus-cli", "build", "prom-cli")
        cmd = " -a \"setModulationFrequency %d.\"" %(enable)
        prom_cli0 = prom_cli + cmd + " -i 0 | hexdump"
        prom_cli1 = prom_cli + cmd + " -i 1 | hexdump"
        # Timer may be required
        os.system(prom_cli0)
        os.system(prom_cli1)
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
        os.system(prom_cli0)
        os.system(prom_cli1)
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
        os.system(prom_cli0)
        os.system(prom_cli1)
    else:
        print("Invalid input to enable imaging")
