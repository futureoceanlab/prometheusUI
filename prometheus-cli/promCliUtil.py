# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Created on Fri Aug 16 19:52:17 2019

@author: jake
"""

import os
import csv
from datetime import datetime
import numpy as np
#import matplotlib.pyplot as plt
#import threading
import time
import promapi as papi
import multiprocessing as mp
import struct
import statistics

class captureSetting:
    
    def __init__(
            self,
            mode=None,
            piDelay=None,
            exposureTime=None,
            modFreq=None,
            dll=None,
            measureTemp=False
            ):
        self.mode = mode
        self.piDelay=piDelay
        self.exposureTime=exposureTime
        self.modFreq=modFreq
        self.dll=dll
        self.measureTemp = measureTemp
        
    def listCmds(self, prevSet=None):
        cmdlist = []
        if (prevSet is None):
            prevSet = captureSetting()
        prevAtts = vars(prevSet)
        currAtts = vars(self)
        keys = list(currAtts.keys())
        #Treat temperature measurement differently
        keys.remove('measureTemp')
        if not(currAtts['mode'] == prevAtts['mode']):
            prevAtts['exposureTime'] = None
        for key in keys:
            if not(currAtts[key] == prevAtts[key]):
                cmdlist.append(self.attrCmd(key, currAtts[key]))
        #cmdlist.append(self.imgCmd())
        return cmdlist
    
    def attrCmd(self, key, val):
        valDict = {
                "mode": "loadConfig {}",
                "piDelay": "enablePiDelay {}",
                "modFreq": "setModulationFrequency {}",
                "dll": "writeRegister 73 {}"}
        if (key == "exposureTime"):
            if (self.mode == 0):
                return "setIntegrationTime2D {}".format(val)
            else:
                return "setIntegrationTime3D {}".format(val)
        else:
            return valDict[key].format(val)
            
        
    def imgCmd(self):
        if (self.mode == 1):
            return "getDCSSorted"
        else:
            return "getBWSorted"
        

class promSession:
    
    def __init__(
            self,
            startupfilename='startupcommands.txt',
            metadatafilename='capturemetadata.csv',
            outputpath= '../../images',
            buildpath='./build',
            cams=[0, 1],
            currSet = None,
            debugMode = False,
            verbosity = 1,
            framerate = 6,
            HDRvideopause = 0
            ):

        #Populate self from input args
        self.debugMode = debugMode
        self.verbosity = mp.Value('i')
        self.verbosity.value = verbosity
        self.cams = cams
        self.debugMode = debugMode
        self.framerate = framerate
        self.HDRvideopause = HDRvideopause
        self.outputpath = os.path.abspath(os.path.normpath(outputpath))
        if currSet is None:
            self.currSet = captureSetting()
        else:
            self.currSet = currSet
        
        #Populate self with tracking variables
        self.numimages=0
        self.numframes=0
        self.numvideos=0
        self.frametag = 'single'
        self.currvideo = -1
        self.filenames = list()
        self.timestamp = datetime.now().strftime('%y%m%d%H%M')

        #Start filesaving and drawing workers
        os.system('taskset -cp 0 {0:d}'.format(os.getpid()))
        os.system('sudo renice -n -10 -p {0:d}'.format(os.getpid()))
        self.filequeue = mp.Queue()   
        mp.Process(target= startsaving, args = (self.filequeue,self.outputpath,metadatafilename, self.verbosity)).start()
        self.analqueue = mp.Queue()
        mp.Process(target= startanalysis, args = (self.analqueue, self.verbosity)).start()

        #Save first metadata line
        self.metawrite(['Filename','Time','Camera','filenum','framenum','vidnum','frametag'] + list(vars(self.currSet).keys()) + ['Temp'])
        
        #Startup the server
        self.startup(startupfilename,cams)

    def startup(self,startupfile,cams):
        with open(startupfile, "r") as log:
    	    cmd = log.readline().strip('\n')
    	    while cmd:
                self.writecommand(cmd)
                cmd = log.readline().strip('\n')        

    def shutdown(self):
        self.filequeue.put(['EOF'])
        self.drawqueue.put(['EOF'])
    
    def writecommand(self,commandstring, cams = None, savefile = None, drawimage = None):
        ret = []
        if cams is None:
            cams = self.cams
        if self.debugMode:
            print(commandstring)
        else: 
            for camnum in cams:                
                response = papi.apiCall(commandstring, camnum)
                if savefile is None:
                    ret.append(response[0])
                else:                    
                    self.enqueue(savefile, response[0])
                    ret.append(response[1])
                    if drawimage is not None:
                        if self.verbosity.value > 1:
                            print('Sending image to queue')                        
                        self.drawqueue.put([drawimage, response[0]])
        if (savefile is None) and (self.verbosity.value > 1):
            print('{}: {}'.format(commandstring,[b.hex() for b in ret]))   
        return ret

    def metawrite(self, row):
        self.filequeue.put(['metadata',row])
            
    def enqueue(self, savefile, data):
        self.filequeue.put([savefile,data])
        
    def enabledll(self):
        self.writecommand('w ae 4')
        
    def disabledll(self):
        self.writecommand('w ae 1')
        
    def captureImage(self,capSet,framenum=None, filename=None, makedrawing = False):        
        #This is a bit of funky logic to allow captureHDRImage to make calls to capture Image                 
        self.numimages = self.numimages + 1
        if (framenum is None):                
            self.numframes = self.numframes + 1
            framenum = self.numframes
        if (filename is None):
            self.frametag = 'single'
            filename = 'image{0}_{1:03d}'.format(self.timestamp,self.numframes)
        #
        cmdlist = capSet.listCmds(self.currSet)
        imgCmd = capSet.imgCmd()        
        self.updateCapSet(capSet)
        #
        if capSet.measureTemp:
            currTemp = self.getTemp()
        else:
            currTemp = None
        #
        for cmd in cmdlist:                
            self.writecommand(cmd)
        capAtts = vars(capSet)   
        if makedrawing is not False:
            if capSet.mode == 0:
                drawtype = 'grayscale'
            elif capSet.mode == 1:
                drawtype = 'DCS'
        else:
            drawtype = None
        for i in range(len(self.cams)):
            camnum = self.cams[i]
            if currTemp is None:
                camtemp = None
            else:
                camtemp = currTemp[i]
            fullfname = '{}_{}.bin'.format(filename,camnum)
            self.writecommand(imgCmd, [camnum], fullfname, drawtype)
            self.filenames.append(fullfname)               
            self.metawrite([fullfname, datetime.now().strftime('%H%M%S.%f)')[:-3], camnum, self.numimages, framenum, str(self.currvideo), self.frametag] + list(capAtts.values()) + [camtemp])
            
    def captureHDRVideo(self,capSets,nImag):
        self.numvideos = self.numvideos + 1
        self.currvideo = self.numvideos        
        for j in range(0, nImag):
            lastimagetime = self.captureHDRImage(capSets)
            if self.verbosity.value > 0:
                print('Finished HDR Image Capture {} of {}'.format(j+1, nImag))
            if self.HDRvideopause > 0:
                pausetime = self.HDRvideopause - (time.time() - lastimagetime)
                if pausetime > 0:
                    time.sleep(pausetime)
                elif self.verbosity.value > 0:
                    print('Cannot keep up with HDR pause, fell behind by {}'.format(pausetime))
        self.currvideo = -1
        if self.verbosity.value > 0:
            print('Finished HDR Video Capture')

    def captureHDRImage(self,capSets):
        self.numframes = self.numframes + 1
        self.frametag = 'HDR'
        for i in range(0,len(capSets)):
                filename = 'image{0}_{1:03d}-{2:02d}'.format(self.timestamp,self.numframes, i)
                if i == len(capSets) - 1:
                    lastimagestart = time.time()
                imagestart = time.time()
                self.captureImage(capSets[i], self.numframes, filename)
                if self.framerate > 0:
                    pausetime = 1/self.framerate - (time.time() - imagestart)
                    if pausetime > 0:
                        time.sleep(pausetime)
                    elif self.verbosity.value > 0:
                        print('Cannot keep up with framerate, fell behind by {}'.format(pausetime))

        if self.verbosity.value > 0 and self.currvideo == -1:
            print('Finished HDR Image Capture')
        return lastimagestart

    def captureVideo(self,capSet,nImag):
        self.numvideos = self.numvideos + 1
        self.currvideo = self.numvideos
        for _ in range(nImag):
            self.captureImage(capSet)
        if self.verbosity.value > 0:
            print('Finished Video Capture')

        
    def captureCalImage(self, numframes=10, exposureTime=3000, calTemp=None):
        self.enabledll()
        cS = self.calCapSet(exposureTime)
        if calTemp is not None:
            self.preHeat(calTemp)
        self.captureHDRVideo(cS, numframes)
        self.disabledll()
        if self.verbosity.value > 0:
            print('Finished Calibration Capture')            

    def calTemperatureSweep(self, nframes, exTime, framerates, breaktime):
        startrate = self.framerate
        for rate in framerates:
            self.framerate = rate
            self.captureCalImage(nframes, exTime)
            time.sleep(breaktime)
        self.framerate = startrate
        if self.verbosity.value > 0:
            print('Finished Calibration Temperature Sweep')

    def updateCapSet(self,newcapSet):
        capAtts = vars(newcapSet)
        for attkey in capAtts.keys():
            if not(capAtts[attkey] is None):
                setattr(self.currSet,attkey,capAtts[attkey])                        
        
    def getTemp(self):
        tempCmd = 'getTemperature'
        tempbytes = self.writecommand(tempCmd)
        numtemps = 4
        camtemps = []
        for cam in tempbytes:
            temps = struct.unpack('<HHHHHH',cam)
            camtemps.append(statistics.mean(temps[0:numtemps])/10)
        if self.verbosity.value > 1:
            print('Camera temp(s): {}'.format(camtemps))
        return camtemps
        #temps = np.zeros(numtemps)
        #for i in range(0,numtemps):
        #    temps[i] = int.from_bytes(tempbytes[2*i:2*(i+1)],'little')
        #return temps.mean()/10
    
    def preHeat(self, targettemp, camnum = None):
        maxcycles = 20
        cycletime = 1
        temps = []
        if camnum is None:
            camind = 0
        else:
            camind = self.cams.index(camnum)            
        temps.append(self.getTemp()[camind])
        i = 0        
        while temps[-1] < targettemp and i < maxcycles:            
            self.illumDisable()
            self.writecommand('w a4 3')
            time.sleep(cycletime)
            self.writecommand('w a4 0')
            temps.append(self.getTemp()[camind])
            i = i+1
        if self.verbosity.value > 0:
            print('Start: {}, End: {}, Cycles: {}'.format(temps[0],temps[-1],i))
            print(temps)
        self.illumEnable()

    def illumDisable(self):
        self.writecommand('w 90 c8')
        if self.verbosity.value > 0:
            print('Illumination Disabled')
        
    def illumEnable(self):
        self.writecommand('w 90 cc')
        if self.verbosity.value > 0:
            print('Illumination Enabled')

    def hexdump(self, chararray):
        outline = ''
        for i in range(0,int(len(chararray)/2)):
            outline = outline + '{:02x}{:02x} '.format(chararray[2*i+1], chararray[2*i])
        print(outline)
        
    def calCapSet(self, exposureTime):
        capvals = {'mode': 1, 'piDelay': 1, 'exposureTime': exposureTime, 'modFreq': 1,'measureTemp':False, 'dll':0}
        capSet = list()
        for i in range(0,50):
            capvals['dll'] = format(i,'x')
            capSet.append(captureSetting(**capvals))
        capvals['mode'] = 0
        capvals['measureTemp'] = True
        capSet.append(captureSetting(**capvals))
        return capSet
    
    
    def meanDCS(self, filename):
        raw = np.fromfile(filename, dtype='uint16')
        DCS = raw.astype('int32') - 2**11
        DCS = np.absolute(DCS)
        DCS = DCS.reshape(320,240,-1).transpose(1,0,2)
        amp = DCS.mean(axis=2)
        print('Mean pixel amplitude is {}'.format(amp.mean().round(2)))
        
def startsaving(q, outputpath, metadatafilename, verbosity):
    os.system('taskset -cp 1 {0:d}'.format(os.getpid()))
    os.system('sudo renice -n -10 -p {0:d}'.format(os.getpid()))
    metafile = open(os.path.join(outputpath, metadatafilename),'a',newline='')
    metawriter = csv.writer(metafile) 
    keepgoing = True
    while keepgoing:
        message = q.get()    
        filename = message[0]
        if verbosity.value > 1:
            print('File Saver got filename {}'.format(filename))
        if filename == 'EOF':
            data = None
            keepgoing = False
            if verbosity.value > 0:
                print('File Saver caught EOF, shutting down')
            metafile.close()
        elif filename == 'metadata':
            data = message[1]
            metawriter.writerow(data)
        else:            
            data = message[1]
            if verbosity.value > 1:
                print('writing data, save queue = {}'.format(q.qsize()))
            f = open('/home/pi/images/' + filename,'wb')
            f.write(data)
            f.close
            if verbosity.value > 1:
                print('wrote data')
        del message,filename,data

def startanalysis(q, verbosity):
    os.system('taskset -cp 2 {0:d}'.format(os.getpid()))
    os.system('sudo renice -n -10 -p {0:d}'.format(os.getpid()))
    import matplotlib.pyplot as plt
    time.sleep(3)
    #if verbosity.value > 1:
    #    print('Tried to plot a straight line')
    #    plt.savefig('WorkerTest')
    keepgoing = True
    while keepgoing:
        message = q.get()
        imagetype = message[0]
        if verbosity.value > 1:            
            print('Analysis Workergot message {}'.format(message[0]))
        if imagetype == 'EOF':
            bytedata = None
            keepgoing = False
            if verbosity.value > 0:
                print('Analysis Workercaught EOF, shutting down')
        elif imagetype == 'grayscale':
            bytedata = message[1]
            data = np.frombuffer(bytedata, dtype=np.uint16)
            data = np.transpose(data.reshape(320, 240, order='F'),(1,0))
            plt.imshow(data)
            #plt.show(block=False)
            plt.savefig('GrayImage')
            if verbosity.value > 1:
                print('Analysis Workertried to draw an image')
        else:
            print("Analysis Workerdoesn't know about imagetype {}".format(imagetype))
        del message,imagetype, bytedata
